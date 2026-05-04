# app/agent/state.py

from langgraph.graph.message import MessagesState
from typing import Optional
from enum import Enum


class MessageType(str, Enum):
    TEXT = "text"
    AUDIO = "audio"
    IMAGE = "image"
    DOCUMENT = "document"


class AgentState(MessagesState):
    # MessagesState already provides:
    # messages: Annotated[list[AnyMessage], add_messages]

    # ─── Core Identity ────────────────────────────────────────────────────
    client_phone: str
    message_type: MessageType
    message_count: int

    # ─── Memory ───────────────────────────────────────────────────────────
    summary: str
    # Rolling compressed summary of everything before current 20 messages.
    # Updated by summarize_node. Injected into system prompt every turn.

    memory_context: str
    # Assembled string built from retrieved_memories ready to inject
    # directly into the system prompt. Saves the LLM node from having
    # to join the list itself.
    # e.g. "- Client rejected ground floor\n- Budget max $500k\n- ..."

    # ─── Client Profile ───────────────────────────────────────────────────
    client_name: str
    client_email: Optional[str]
    client_timezone: str
    onboarding_complete: bool

    # ─── Onboarding Tracking ──────────────────────────────────────────────
    onboarding_attempts: dict          # { field_name: int } — auto-skip budget after 3
    onboarding_missing_fields: list    # ["name", "city", ...] — drives llm_node prompt

    # ─── Tool Loop Guard ─────────────────────────────────────────────────
    tool_call_count: int               # reset each turn, caps runaway tool loops

    # ─── Documents ────────────────────────────────────────────────────────
    active_documents: dict
    # { "doc_id": { "filename", "doc_type", "page_count", "storage", "expires_at" } }

    injected_document_text: Optional[str]
    # Full text of small docs (< 3000 tokens) injected directly into prompt.
    # None when doc was chunked into ChromaDB instead.

    # ─── Raw Media (transient) ────────────────────────────────────────────
    media_id: Optional[str]
    # WhatsApp media ID for audio, image, or document messages.
    # Used by downstream nodes to fetch the file from WhatsApp media API.

    media_filename: Optional[str]
    # Original filename for document messages only.

    audio_buffer: Optional[bytes]
    # Raw audio bytes downloaded from WhatsApp media API.
    # Populated in audio module before STT runs.
    # Cleared after STT converts it to text and updates messages.

    image_path: Optional[str]
    # Local path to downloaded image file.
    # Populated in image module before vision runs.
    # Cleared after vision extracts description and updates messages.


    # ─── Escalation & Response ────────────────────────────────────────────
    escalated: bool
    response_type: str
    # "text" or "audio" — LLM decides before generating its reply.