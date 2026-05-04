import uuid
from typing import Optional
from langchain_core.documents import Document
from src.agent.modules.memory.chroma_client  import get_collection

COLLECTION_NAME = "company_knowledge"


def _get_store():
    return get_collection(COLLECTION_NAME)


def store_company_chunk(
    doc_id: str,
    chunk_index: int,
    text: str,
    doc_type: str,
    filename: str
) -> None:
    """
    Store a single chunk from a company document.

    Args:
        doc_id: Unique document ID — same across all chunks of one document
        chunk_index: Position of this chunk within the document
        text: The chunk text content
        doc_type: property_listing, area_guide, policy, faq, developer_profile, legal
        filename: Original filename for reference
    """
    store = _get_store()

    doc = Document(
        page_content=text,
        metadata={
            "id": f"{doc_id}_chunk_{chunk_index}",
            "doc_id": doc_id,
            "chunk_index": chunk_index,
            "doc_type": doc_type,
            "filename": filename,
            "source": "company"
        }
    )

    store.add_documents([doc])


def search_company_knowledge(
    query: str,
    k: int = 4,
    doc_type: Optional[str] = None
) -> list[str]:
    """
    Search company knowledge base by semantic similarity.

    Args:
        query: What to search for
        k: Number of results
        doc_type: Optional filter by document type

    Returns:
        List of relevant chunk text strings
    """
    store = _get_store()

    filter_dict = {"source": "company"}
    if doc_type:
        filter_dict["doc_type"] = doc_type

    retriever = store.as_retriever(
        search_type="similarity",
        search_kwargs={
            "k": k,
            "filter": filter_dict
        }
    )

    docs = retriever.invoke(query)
    return [doc.page_content for doc in docs]


def delete_company_document(doc_id: str) -> None:
    """Delete all chunks belonging to a specific document."""
    store = _get_store()

    results = store.get(where={"doc_id": doc_id})
    if results and results["ids"]:
        store.delete(ids=results["ids"])