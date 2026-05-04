# src/graph/nodes/document_node.py

import uuid
import io
import traceback
from datetime import datetime, timedelta
import tiktoken
from src.agent.state import AgentState, MessageType
from src.agent.modules.memory.long_term_client_memory import store_client_chunk
from src.db.session import get_async_session
from src.app.models.client_document import ClientDocument, StorageStatus, ClientDocType
from config import Config
import httpx

from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
import tempfile
import os

_encoder = tiktoken.get_encoding("cl100k_base")

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
INJECT_THRESHOLD = 3000
FILE_SIZE_LIMIT_MB = 15
PAGE_LIMIT = 40


def count_tokens(text: str) -> int:
    return len(_encoder.encode(text))


def chunk_text(text: str) -> list[str]:
    tokens = _encoder.encode(text)
    chunks = []
    start = 0
    while start < len(tokens):
        end = start + CHUNK_SIZE
        chunks.append(_encoder.decode(tokens[start:end]))
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks


def detect_file_type(filename: str, file_bytes: bytes) -> str:
    """
    Detect file type from filename extension first,
    then fall back to magic bytes if extension is missing/ambiguous.
    Returns: 'pdf', 'docx', or 'unsupported'
    """
    if filename:
        lower = filename.lower()
        if lower.endswith(".pdf"):
            return "pdf"
        if lower.endswith(".docx"):
            return "docx"
        if lower.endswith(".doc"):
            return "doc"

    # Fallback: magic bytes
    if file_bytes[:4] == b"%PDF":
        return "pdf"
    # DOCX is a ZIP archive starting with PK
    if file_bytes[:2] == b"PK":
        return "docx"

    return "unsupported"


async def load_pdf_text(file_bytes: bytes) -> tuple[str, int]:
    """
    Write bytes to a temp file, load with PyPDFLoader.
    Returns (extracted_text, page_count).
    """
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        loader = PyPDFLoader(tmp_path)
        pages = loader.load()
        page_count = len(pages)
        full_text = "\n\n".join(p.page_content for p in pages)
        return full_text, page_count
    finally:
        os.unlink(tmp_path)


async def load_docx_text(file_bytes: bytes) -> tuple[str, int]:
    """
    Write bytes to a temp file, load with Docx2txtLoader.
    Returns (extracted_text, estimated_page_count).
    Page count is estimated since DOCX has no hard page concept.
    """
    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        loader = Docx2txtLoader(tmp_path)
        docs = loader.load()
        full_text = "\n\n".join(d.page_content for d in docs)
        # Rough page estimate: ~3000 chars per page
        estimated_pages = max(1, len(full_text) // 3000)
        return full_text, estimated_pages
    finally:
        os.unlink(tmp_path)


async def fetch_media_bytes(media_id: str) -> bytes:
    async with httpx.AsyncClient() as client:
        url_resp = await client.get(
            f"https://graph.facebook.com/v19.0/{media_id}",
            headers={"Authorization": f"Bearer {Config.WHATSAPP_TOKEN}"},
        )
        url_resp.raise_for_status()
        media_url = url_resp.json()["url"]

        file_resp = await client.get(
            media_url,
            headers={"Authorization": f"Bearer {Config.WHATSAPP_TOKEN}"},
        )
        file_resp.raise_for_status()
        return file_resp.content


async def document_node(state: AgentState) -> dict:
    """
    Runs on every turn but exits immediately if message_type is not DOCUMENT.
    Supports PDF and DOCX via LangChain loaders.
    Downloads → detects type → extracts text → inject or chunk → updates state.
    Document chunks live for 3 days then deleted by APScheduler.
    """
    if state.get("message_type") != MessageType.DOCUMENT:
        return {}

    media_id = state.get("media_id")
    filename = state.get("media_filename") or ""
    phone = state["client_phone"]

    if not media_id:
        return {}

    try:
        file_bytes = await fetch_media_bytes(media_id)

        # ─── size guard ───────────────────────────────────────────────────
        size_mb = len(file_bytes) / (1024 * 1024)
        if size_mb > FILE_SIZE_LIMIT_MB:
            return {
                "injected_document_text": (
                    f"[SYSTEM INSTRUCTION]: The user's document is {size_mb:.1f} MB, "
                    f"which exceeds the 15 MB limit. "
                    "Politely ask them to send a smaller version or paste the key section directly."
                )
            }

        # ─── detect file type ─────────────────────────────────────────────
        file_type = detect_file_type(filename, file_bytes)

        if file_type == "unsupported" or file_type == "doc":
            return {
                "injected_document_text": (
                    "[SYSTEM INSTRUCTION]: The user sent a file in an unsupported format. "
                    "Supported formats are PDF and DOCX. "
                    "If they sent a .doc file, ask them to re-save it as .docx or PDF. "
                    "Politely explain this and ask them to resend in a supported format."
                )
            }

        # ─── extract text via appropriate loader ──────────────────────────
        if file_type == "pdf":
            extracted_text, page_count = await load_pdf_text(file_bytes)
        else:
            extracted_text, page_count = await load_docx_text(file_bytes)

        # ─── page count guard (PDF only — DOCX estimate is already rough) ─
        if file_type == "pdf" and page_count > PAGE_LIMIT:
            return {
                "injected_document_text": (
                    f"[SYSTEM INSTRUCTION]: The user's PDF has {page_count} pages, "
                    f"which exceeds the {PAGE_LIMIT}-page limit. "
                    "Politely ask them to share only the specific section they need help with."
                )
            }

        # ─── guard against empty extraction ───────────────────────────────
        if not extracted_text or not extracted_text.strip():
            return {
                "injected_document_text": (
                    "[SYSTEM INSTRUCTION]: The document was received but no text could be extracted. "
                    "It may be a scanned image PDF with no OCR layer, or an empty file. "
                    "Politely ask the client to send a text-based PDF or DOCX, "
                    "or paste the content directly into the chat."
                )
            }

        token_count = count_tokens(extracted_text)
        doc_id = str(uuid.uuid4())

        # 3 day TTL — APScheduler will clean up after this
        expires_at = datetime.utcnow() + timedelta(days=3)

        # ─── small doc → inject directly into prompt ──────────────────────
        if token_count <= INJECT_THRESHOLD:
            async with get_async_session() as session:
                session.add(
                    ClientDocument(
                        doc_id=doc_id,
                        client_phone=phone,
                        filename=filename,
                        doc_type=ClientDocType.OTHER,
                        page_count=page_count,
                        token_count=token_count,
                        storage_status=StorageStatus.INJECTED,
                        expires_at=expires_at,
                        chunks_cleared=False,
                    )
                )
                await session.commit()

            active_documents = dict(state.get("active_documents") or {})
            active_documents[doc_id] = {
                "filename": filename,
                "page_count": page_count,
                "storage": "injected",
                "expires_at": expires_at.timestamp(),
            }

            return {
                "active_documents": active_documents,
                "injected_document_text": extracted_text,
            }

        # ─── large doc → chunk into ChromaDB with 3 day TTL ──────────────
        chunks = chunk_text(extracted_text)

        for i, chunk in enumerate(chunks):
            store_client_chunk(
                phone_number=phone,
                doc_id=doc_id,
                chunk_index=i,
                text=chunk,
                filename=filename,
                expires_at=int(expires_at.timestamp()),
            )

        async with get_async_session() as session:
            session.add(
                ClientDocument(
                    doc_id=doc_id,
                    client_phone=phone,
                    filename=filename,
                    doc_type=ClientDocType.OTHER,
                    page_count=page_count,
                    token_count=token_count,
                    storage_status=StorageStatus.CHUNKED,
                    expires_at=expires_at,
                    chunks_cleared=False,
                )
            )
            await session.commit()

        active_documents = dict(state.get("active_documents") or {})
        active_documents[doc_id] = {
            "filename": filename,
            "page_count": page_count,
            "storage": "chunked",
            "expires_at": expires_at.timestamp(),
        }

        return {
            "active_documents": active_documents,
            "injected_document_text": None,
        }

    except Exception:
        traceback.print_exc()
        return {
            "injected_document_text": (
                "[SYSTEM INSTRUCTION]: The document processing failed unexpectedly. "
                "Politely tell the client you had trouble reading the file and ask them "
                "to try sending it again as a standard PDF or DOCX."
            )
        }