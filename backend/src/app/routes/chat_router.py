from fastapi import APIRouter, Depends, status, Request, Query, Response
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from src.agent.graph.graph import build_graph
from config import Config
from sqlmodel.ext.asyncio.session import AsyncSession
from src.db.session import get_db_session as get_session
from src.app.services.chat_service import ChatService
from src.app.dependencies.bearer import AccessTokenBearer
from src.app.schemas.chat_schema import ChatSendRequest, ChatSendResponse
from src.db.redis import mark_whatsapp_message_seen
from fastapi.exceptions import HTTPException
from typing import Optional

service = ChatService()
chat_router = APIRouter()


# ─── Session Listing (read-only) ──────────────────────────────────────────────

@chat_router.get("/sessions")
async def list_sessions(
    client_phone: Optional[str] = None,
    offset: int = 0,
    limit: int = 20,
    token_data: dict = Depends(AccessTokenBearer()),
    session: AsyncSession = Depends(get_session),
):
    sessions = await service.list_sessions(session, client_phone, offset, limit)
    return [s.model_dump() for s in sessions]


@chat_router.get("/sessions/{session_id}")
async def get_session_detail(
    session_id: str,
    token_data: dict = Depends(AccessTokenBearer()),
    session: AsyncSession = Depends(get_session),
):
    conv_session = await service.get_session(session_id, session)
    if not conv_session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return conv_session.model_dump()

@chat_router.get("/sessions/{session_id}/transcripts")
async def get_session_transcripts(
    session_id: str,
    token_data: dict = Depends(AccessTokenBearer()),
    session: AsyncSession = Depends(get_session),
):
    import uuid
    try:
        session_uuid = uuid.UUID(session_id)
        transcripts = await service.get_session_transcripts(session_uuid, session)
        return [t.model_dump() for t in transcripts]
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID format")

@chat_router.get("/stats/monthly")
async def get_monthly_session_stats(
    token_data: dict = Depends(AccessTokenBearer()),
    session: AsyncSession = Depends(get_session),
):
    """Get session stats for current and previous month for response time comparison"""
    from datetime import datetime, timedelta
    now = datetime.utcnow()
    current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_month_start = (current_month_start - timedelta(days=32)).replace(day=1)
    last_month_end = current_month_start - timedelta(microseconds=1)
    
    current_sessions = await service.get_sessions_by_date_range(session, current_month_start, now)
    last_month_sessions = await service.get_sessions_by_date_range(session, last_month_start, last_month_end)
    
    # Calculate average response times from actual session latency data
    current_total_latency = sum((s.total_latency_ms or 0) for s in current_sessions) / 1000
    last_month_total_latency = sum((s.total_latency_ms or 0) for s in last_month_sessions) / 1000
    current_avg_response = current_total_latency / len(current_sessions) if current_sessions else 1.2
    last_month_avg_response = last_month_total_latency / len(last_month_sessions) if last_month_sessions else 1.5
    
    return {
        "current_month": {
            "total_sessions": len(current_sessions),
            "avg_response_time": current_avg_response
        },
        "last_month": {
            "total_sessions": len(last_month_sessions),
            "avg_response_time": last_month_avg_response
        }
    }


# ─── Send message to AI agent ────────────────────────────────────────────────

@chat_router.post("/send", response_model=ChatSendResponse)
async def send_message(
    request: Request, 
    data: ChatSendRequest,
    token_data: dict = Depends(AccessTokenBearer()),
    db_session: AsyncSession = Depends(get_session),
):
    """
    Send a text message to the AI agent on behalf of a client.
    The agent processes the message through the full LangGraph pipeline
    (profile_loader → onboarding → memory → document → llm → tools → response)
    and returns the agent's reply.
    """
    graph = request.app.state.graph

    # Build the WhatsApp-format payload that the agent graph expects
    payload = {
        "entry": [{
            "changes": [{
                "value": {
                    "messages": [{
                        "from": data.client_phone,
                        "type": "text",
                        "text": {"body": data.message}
                    }]
                }
            }]
        }]
    }
    # Ensure interaction counts are logged and fetch the session for callback binding
    active_session = await service.log_interaction(db_session, data.client_phone, escalated=False)

    config = {
        "configurable": {
            "thread_id": data.client_phone,
            "incoming_payload": payload,
        }
    }

    if active_session:
        from src.agent.utils.callbacks import AgentLoggingCallback
        config["callbacks"] = [
            AgentLoggingCallback(client_phone=data.client_phone, session_id=active_session.session_id)
        ]

    result = await graph.ainvoke({"messages": []}, config=config)

    # Extract the agent's reply from the result
    agent_reply = ""
    for msg in reversed(result.get("messages", [])):
        if hasattr(msg, "content") and msg.content:
            has_tool_calls = hasattr(msg, "tool_calls") and msg.tool_calls
            if not has_tool_calls:
                agent_reply = msg.content
                break

    escalated = result.get("escalated", False)
    
    # Update escalation flag if needed
    if escalated and active_session:
        active_session.escalated = True
        try:
            db_session.add(active_session)
            await db_session.commit()
        except Exception:
            await db_session.rollback()

    # Fire-and-forget transcript saving - save both user message and AI response
    if active_session:
        import time
        start_time = time.time()
        
        # Save user message transcript
        service.save_transcript_fire_and_forget(
            session_id=active_session.session_id,
            client_phone=data.client_phone,
            message_content=data.message,
            message_type="user",
            tokens_used=None,
            processing_time_ms=None
        )
        
        # Save AI response transcript
        processing_time_ms = int((time.time() - start_time) * 1000)
        service.save_transcript_fire_and_forget(
            session_id=active_session.session_id,
            client_phone=data.client_phone,
            message_content=agent_reply,
            message_type="assistant",
            tokens_used=result.get("tokens_used", None),
            processing_time_ms=processing_time_ms
        )

    return ChatSendResponse(
        client_phone=data.client_phone,
        user_message=data.message,
        agent_reply=agent_reply,
        response_type=result.get("response_type", "text"),
        onboarding_complete=result.get("onboarding_complete", False),
        escalated=escalated,
        message_count=result.get("message_count", 0),
    )


# ─── WhatsApp Webhook (Meta Graph API) ───────────────────────────────────────

@chat_router.get("/webhook")
async def verify_webhook(
    request: Request,
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
):
    """
    Webhook verification route for WhatsApp (Facebook Graph API).
    """
    if hub_mode == "subscribe" and hub_verify_token == Config.WHATSAPP_VERIFY_TOKEN:
        return Response(content=hub_challenge, media_type="text/plain", status_code=200)
    raise HTTPException(status_code=403, detail="Verification token mismatch")


@chat_router.post("/webhook")
async def handle_whatsapp_webhook(request: Request):
    """
    Handles incoming messages from WhatsApp Cloud API.
    Replies directly to the user via Facebook Graph API POST.
    """
    try:
        body = await request.json()
    except Exception:
        return Response("Bad Request", status_code=400)
    
    if body.get("object") != "whatsapp_business_account":
        return Response(status_code=404)
        
    try:
        entry = body["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]
        
        # WhatsApp sends status updates (delivered, read) as well. Ignore those.
        if "messages" not in value:
            return Response("OK", status_code=200)
            
        whatsapp_message = value["messages"][0]
        client_phone = whatsapp_message["from"]
        message_id = whatsapp_message.get("id")
        
        if whatsapp_message["type"] not in {"text", "audio", "image", "document", "application"}:
            return Response("OK", status_code=200)

        if message_id:
            try:
                if not await mark_whatsapp_message_seen(message_id):
                    return Response("OK", status_code=200)
            except Exception:
                pass
        
    except (KeyError, IndexError):
        # Ignore malformed requests rather than failing
        return Response("OK", status_code=200)

    from src.worker.tasks import process_whatsapp_message_task
    process_whatsapp_message_task.delay(body)

    # Acknowledge receipt to Meta immediately (status 200 OK)
    return Response("OK", status_code=200)
