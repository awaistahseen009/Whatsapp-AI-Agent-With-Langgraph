import uuid
from datetime import datetime
from typing import Optional
from langchain_core.documents import Document
from src.agent.modules.memory.chroma_client import get_collection

COLLECTION_NAME = "client_memories"
DOCUMENT_CHUNKS_COLLECTION = "client_documents"


def _get_memory_store():
    return get_collection(COLLECTION_NAME)


def _get_document_store():
    return get_collection(DOCUMENT_CHUNKS_COLLECTION)


# ─── Client Memory Store ──────────────────────────────────────────────────────

def store_client_memory(
    phone_number: str,
    fact: str,
    raw_context: str,
    memory_type: str
) -> None:
    """
    Store a memory fact enriched with the raw conversation context it came from.

    The embedded text is: fact + raw_context joined together.
    This makes retrieval richer — searching for "school district" will surface
    memories even if the fact itself only says "has two kids".

    Args:
        phone_number:  Client's WhatsApp number
        fact:          Single extracted fact e.g. "Client rejected ground floor"
        raw_context:   The raw conversation chunk this fact was extracted from
        memory_type:   preference, rejection, personal, financial, property_viewed
    """
    store = _get_memory_store()

    # embed fact + raw context together for richer retrieval
    enriched_text = f"{fact}\n\nContext: {raw_context}"

    doc = Document(
        page_content=enriched_text,
        metadata={
            "id": str(uuid.uuid4()),
            "phone_number": phone_number,
            "fact": fact,                    # clean fact stored in metadata
            "memory_type": memory_type,
            "source": "client",
            "timestamp": datetime.utcnow().isoformat()
        }
    )

    store.add_documents([doc])


def search_client_memories(
    phone_number: str,
    query: str,
    k: int = 6
) -> list[str]:
    """
    Search memories for a specific client.
    Returns only the clean fact from metadata, not the full enriched text.
    """
    store = _get_memory_store()

    retriever = store.as_retriever(
        search_type="similarity",
        search_kwargs={
            "k": k,
            "filter": {"phone_number": phone_number}
        }
    )

    docs = retriever.invoke(query)
    # return the clean fact, not the enriched embedding text
    return [doc.metadata.get("fact", doc.page_content) for doc in docs]


def delete_client_memories(phone_number: str) -> None:
    store = _get_memory_store()
    results = store.get(where={"phone_number": phone_number})
    if results and results["ids"]:
        store.delete(ids=results["ids"])


# ─── Document Chunk Store ─────────────────────────────────────────────────────

def store_client_chunk(
    phone_number: str,
    doc_id: str,
    chunk_index: int,
    text: str,
    filename: str,
    expires_at: int
) -> None:
    """
    Store a single chunk from a client-sent document.
    Temporary — deleted after 3 days by APScheduler.
    """
    store = _get_document_store()

    doc = Document(
        page_content=text,
        metadata={
            "id": f"{doc_id}_chunk_{chunk_index}",
            "phone_number": phone_number,
            "doc_id": doc_id,
            "chunk_index": chunk_index,
            "filename": filename,
            "source": "client_document",
            "expires_at": expires_at,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

    store.add_documents([doc])


def search_document_chunks(
    phone_number: str,
    doc_id: str,
    query: str,
    k: int = 4
) -> list[str]:
    store = _get_document_store()

    retriever = store.as_retriever(
        search_type="similarity",
        search_kwargs={
            "k": k,
            "filter": {
                "$and": [
                    {"phone_number": phone_number},
                    {"doc_id": doc_id}
                ]
            }
        }
    )

    docs = retriever.invoke(query)
    return [doc.page_content for doc in docs]


def delete_document_chunks(doc_id: str) -> None:
    store = _get_document_store()
    results = store.get(where={"doc_id": doc_id})
    if results and results["ids"]:
        store.delete(ids=results["ids"])


def delete_expired_chunks() -> None:
    """
    Called by APScheduler every 24 hours.
    Deletes all document chunks whose expires_at is in the past.
    """
    store = _get_document_store()
    now = int(datetime.utcnow().timestamp())
    results = store.get(where={"expires_at": {"$lt": now}})
    if results and results["ids"]:
        store.delete(ids=results["ids"])
        print(f"TTL cleanup: deleted {len(results['ids'])} expired document chunks")