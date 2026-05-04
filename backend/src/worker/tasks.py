import asyncio
import sys
from threading import Lock

# Windows psycopg compatibility
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import httpx
from celery.signals import worker_process_shutdown, worker_shutdown
from src.agent.modules.audio.tts.text_to_speech import TTS
from src.worker.celery_app import celery_app
from src.db.session import async_engine, get_async_session
from src.app.services.chat_service import ChatService
from src.agent.graph.graph import build_graph
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from config import Config

service = ChatService()
_worker_loop: asyncio.AbstractEventLoop | None = None
_worker_loop_lock = Lock()
_worker_checkpointer_cm = None
_worker_checkpointer = None
_worker_graph = None


def _get_worker_loop() -> asyncio.AbstractEventLoop:
    """
    Celery tasks are synchronous, but the agent stack is async. Do not use
    asyncio.run() per task: it creates and closes a fresh loop, while asyncpg
    keeps pooled connections bound to the old loop.
    """
    global _worker_loop
    if _worker_loop is None or _worker_loop.is_closed():
        _worker_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_worker_loop)
    return _worker_loop


def _run_on_worker_loop(coro):
    with _worker_loop_lock:
        loop = _get_worker_loop()
        return loop.run_until_complete(coro)


def _close_worker_loop(*args, **kwargs) -> None:
    global _worker_loop, _worker_checkpointer_cm, _worker_checkpointer, _worker_graph
    if _worker_loop is None or _worker_loop.is_closed():
        return

    with _worker_loop_lock:
        if _worker_loop is None or _worker_loop.is_closed():
            return
        if _worker_checkpointer_cm is not None:
            _worker_loop.run_until_complete(
                _worker_checkpointer_cm.__aexit__(None, None, None)
            )
            _worker_checkpointer_cm = None
            _worker_checkpointer = None
            _worker_graph = None
        _worker_loop.run_until_complete(async_engine.dispose())
        _worker_loop.close()
        _worker_loop = None


worker_process_shutdown.connect(_close_worker_loop)
worker_shutdown.connect(_close_worker_loop)

def _make_text_payload(client_phone: str, message_text: str) -> dict:
    return {
        "entry": [{
            "changes": [{
                "value": {
                    "messages": [{
                        "from": client_phone,
                        "type": "text",
                        "text": {"body": message_text}
                    }]
                }
            }]
        }]
    }


async def _send_whatsapp_text(
    client: httpx.AsyncClient,
    client_phone: str,
    text: str,
    headers: dict,
) -> None:
    url = f"https://graph.facebook.com/v19.0/{Config.WHATSAPP_PHONE_ID}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": client_phone,
        "type": "text",
        "text": {"body": text},
    }
    response = await client.post(url, headers={**headers, "Content-Type": "application/json"}, json=payload)
    response.raise_for_status()


async def _send_whatsapp_audio(
    client: httpx.AsyncClient,
    client_phone: str,
    text: str,
    headers: dict,
) -> None:
    audio_bytes = await TTS().convert_to_speech(text=text)
    upload_url = f"https://graph.facebook.com/v19.0/{Config.WHATSAPP_PHONE_ID}/media"
    upload_response = await client.post(
        upload_url,
        headers=headers,
        data={
            "messaging_product": "whatsapp",
            "type": "audio/mpeg",
        },
        files={
            "file": ("friday-reply.mp3", audio_bytes, "audio/mpeg"),
        },
    )
    upload_response.raise_for_status()
    media_id = upload_response.json()["id"]

    send_url = f"https://graph.facebook.com/v19.0/{Config.WHATSAPP_PHONE_ID}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": client_phone,
        "type": "audio",
        "audio": {"id": media_id},
    }
    send_response = await client.post(send_url, headers={**headers, "Content-Type": "application/json"}, json=payload)
    send_response.raise_for_status()


async def _get_worker_graph():
    global _worker_checkpointer_cm, _worker_checkpointer, _worker_graph
    if _worker_graph is not None:
        return _worker_graph

    _worker_checkpointer_cm = AsyncPostgresSaver.from_conn_string(
        Config.LANGGRAPH_CHECKPOINT_DB_URL
    )
    _worker_checkpointer = await _worker_checkpointer_cm.__aenter__()
    await _worker_checkpointer.setup()
    _worker_graph = build_graph(_worker_checkpointer)
    return _worker_graph


async def async_process_whatsapp_message(payload: dict):
    client_phone = payload["entry"][0]["changes"][0]["value"]["messages"][0]["from"]
    config = {
        "configurable": {
            "thread_id": client_phone,
            "incoming_payload": payload,
        }
    }

    async with get_async_session() as db_session:
        active_session = await service.log_interaction(db_session, client_phone, escalated=False)

        if active_session:
            from src.agent.utils.callbacks import AgentLoggingCallback
            config["callbacks"] = [
                AgentLoggingCallback(client_phone=client_phone, session_id=active_session.session_id)
            ]

        graph = await _get_worker_graph()
        result = await graph.ainvoke({"messages": []}, config=config)

        # Process result
        agent_reply = ""
        for msg in reversed(result.get("messages", [])):
            if hasattr(msg, "content") and msg.content:
                has_tool_calls = hasattr(msg, "tool_calls") and msg.tool_calls
                if not has_tool_calls:
                    agent_reply = msg.content
                    break

        escalated = result.get("escalated", False)
        response_type = result.get("response_type", "text")
        
        if escalated and active_session:
            active_session.escalated = True
            try:
                db_session.add(active_session)
                await db_session.commit()
            except Exception:
                await db_session.rollback()

    # Reply to WhatsApp directly
    if agent_reply and getattr(Config, "WHATSAPP_TOKEN", None) and getattr(Config, "WHATSAPP_PHONE_ID", None):
        headers = {
            "Authorization": f"Bearer {Config.WHATSAPP_TOKEN}",
        }
        async with httpx.AsyncClient() as client:
            try:
                if response_type == "audio":
                    await _send_whatsapp_audio(client, client_phone, agent_reply, headers)
                else:
                    await _send_whatsapp_text(client, client_phone, agent_reply, headers)
            except Exception:
                try:
                    await _send_whatsapp_text(client, client_phone, agent_reply, headers)
                except Exception:
                    pass


@celery_app.task(name="process_whatsapp_message_task")
def process_whatsapp_message_task(payload: dict | str, message_text: str | None = None):
    """
    Synchronous Celery task that wraps the async LangGraph process.
    """
    if isinstance(payload, str):
        payload = _make_text_payload(payload, message_text or "")
    _run_on_worker_loop(async_process_whatsapp_message(payload))
