import asyncio
from io import BytesIO

from langchain_core.messages import AIMessage, HumanMessage

from src.agent.graph.nodes.document_node import fetch_media_bytes
from src.agent.modules.audio.stt.speech_to_text import STT
from src.agent.modules.image.image_to_text import ITT
from src.agent.state import AgentState, MessageType


def _get_latest_media_meta(state: AgentState) -> dict:
    messages = state.get("messages") or []
    if not messages:
        return {}
    return getattr(messages[-1], "additional_kwargs", {}) or {}


async def _transcribe_audio(audio_bytes: bytes, filename: str, mime_type: str) -> str:
    response = await asyncio.to_thread(
        lambda: STT().client.audio.transcriptions.create(
            model="whisper-large-v3-turbo",
            file=(filename, BytesIO(audio_bytes), mime_type),
        )
    )
    return response.text


async def _describe_image(image_bytes: bytes, prompt: str) -> str:
    return await asyncio.to_thread(
        lambda: asyncio.run(ITT().convert_image_to_text(image_bytes, prompt=prompt))
    )


async def media_node(state: AgentState) -> dict:
    """
    Turns WhatsApp media payloads into text before profile/onboarding/LLM nodes.
    Documents are handled by document_node later in the graph.
    """
    message_type = state.get("message_type")
    if message_type not in (MessageType.AUDIO, MessageType.IMAGE):
        return {}

    media_id = state.get("media_id")
    if not media_id:
        return {
            "messages": [
                AIMessage(content="I received a media message, but WhatsApp did not include a media ID. Could you send it again?")
            ]
        }

    meta = _get_latest_media_meta(state)
    try:
        media_bytes = await fetch_media_bytes(media_id)

        if message_type == MessageType.AUDIO:
            filename = meta.get("filename") or "voice-message.ogg"
            mime_type = meta.get("mime_type") or "audio/ogg"
            transcript = (await _transcribe_audio(media_bytes, filename, mime_type)).strip()
            content = f"[Voice message transcript]\n{transcript}" if transcript else "[Voice message was empty]"

        else:
            caption = meta.get("caption") or ""
            prompt = (
                "Analyze this WhatsApp image for a real estate assistant. "
                "Describe visible text, property details, rooms, documents, issues, prices, dates, and anything the client may be asking about. "
                "Be factual and concise."
            )
            description = (await _describe_image(media_bytes, prompt)).strip()
            content = f"[Image analysis]\n{description}"
            if caption:
                content += f"\n\nClient caption: {caption}"

        return {
            "messages": [
                HumanMessage(
                    content=content,
                    additional_kwargs={
                        "media_id": media_id,
                        "message_type": message_type.value,
                        "media_processed": True,
                    },
                )
            ]
        }

    except Exception:
        return {
            "messages": [
                AIMessage(content="I had trouble processing that media message. Could you try sending it again?")
            ]
        }
