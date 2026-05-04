from langchain_core.messages import HumanMessage
from src.agent.state import AgentState, MessageType
from langchain_core.runnables import RunnableConfig

def extract_phone(payload: dict) -> str:
    return (
        payload["entry"][0]["changes"][0]["value"]
        ["messages"][0]["from"]
    )


def extract_message_type(payload: dict) -> MessageType:
    msg = payload["entry"][0]["changes"][0]["value"]["messages"][0]
    msg_type = msg.get("type", "text")
    if msg_type == "text":
        return MessageType.TEXT
    elif msg_type == "audio":
        return MessageType.AUDIO
    elif msg_type == "image":
        return MessageType.IMAGE
    elif msg_type in ("document", "application"):
        return MessageType.DOCUMENT
    return MessageType.TEXT


def extract_text_content(payload: dict) -> str:
    msg = payload["entry"][0]["changes"][0]["value"]["messages"][0]
    msg_type = msg.get("type", "text")

    if msg_type == "text":
        return msg["text"]["body"]
    elif msg_type == "image":
        caption = msg.get("image", {}).get("caption", "").strip()
        return f"[Client sent an image] {caption}" if caption else "[Client sent an image]"
    elif msg_type in ("document", "application"):
        caption = msg.get("document", {}).get("caption", "").strip()
        filename = msg.get("document", {}).get("filename", "a document")
        return f"[Client sent {filename}] {caption}" if caption else f"[Client sent {filename}]"
    elif msg_type == "audio":
        return "[Client sent a voice message]"
    return msg.get("text", {}).get("body", "[Unknown message type]")


def extract_media_metadata(payload: dict) -> dict:
    msg = payload["entry"][0]["changes"][0]["value"]["messages"][0]
    msg_type = msg.get("type", "text")
    media_key = "document" if msg_type == "application" else msg_type
    media = msg.get(media_key, {}) if media_key in ("audio", "image", "document") else {}
    return {
        "caption": media.get("caption"),
        "filename": media.get("filename"),
        "mime_type": media.get("mime_type"),
        "sha256": media.get("sha256"),
    }


def extract_media_id(payload: dict) -> str | None:
    msg = payload["entry"][0]["changes"][0]["value"]["messages"][0]
    msg_type = msg.get("type", "text")
    if msg_type == "audio":
        return msg.get("audio", {}).get("id")
    elif msg_type == "image":
        return msg.get("image", {}).get("id")
    elif msg_type in ("document", "application"):
        return msg.get("document", {}).get("id")
    return None


def extract_document_filename(payload: dict) -> str | None:
    msg = payload["entry"][0]["changes"][0]["value"]["messages"][0]
    return msg.get("document", {}).get("filename")


def is_status_update(payload: dict) -> bool:
    try:
        value = payload["entry"][0]["changes"][0]["value"]
        return "statuses" in value and "messages" not in value
    except (KeyError, IndexError):
        return True


async def input_node(state: AgentState, *, config: RunnableConfig) -> dict:
    payload = config["configurable"]["incoming_payload"]

    phone = extract_phone(payload)
    message_type = extract_message_type(payload)
    text_content = extract_text_content(payload)
    media_id = extract_media_id(payload)
    filename = extract_document_filename(payload)
    media_metadata = extract_media_metadata(payload)

    human_message = HumanMessage(
        content=text_content,
        additional_kwargs={
            "media_id": media_id,
            "filename": filename,
            **media_metadata,
            "message_type": message_type.value,
        },
    )

    return {
        "client_phone": phone,
        "message_type": message_type,
        "message_count": state.get("message_count", 0) + 1,
        "messages": [human_message],
        "media_id": media_id,
        "media_filename": filename,
        "tool_call_count": 0,
    }
