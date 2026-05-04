from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type
from src.agent.modules.memory.long_term_client_memory import search_document_chunks


class DocumentSearchInput(BaseModel):
    query: str = Field(description="What to search for in the document")
    doc_id: str = Field(description="The doc_id from active_documents in state")
    phone_number: str = Field(description="Client's WhatsApp phone number")


class DocumentSearchTool(BaseTool):
    name: str = "document_search"
    description: str = (
        "Search the contents of a document the client sent this session. "
        "Only use when active_documents has entries with storage: chunked. "
        "Pass the doc_id exactly as it appears in active_documents."
    )
    args_schema: Type[BaseModel] = DocumentSearchInput

    async def _arun(self, query: str, doc_id: str, phone_number: str) -> str:
        try:
            results = search_document_chunks(
                phone_number=phone_number,
                doc_id=doc_id,
                query=query,
                k=4
            )
            if not results:
                return "No relevant content found in that document for your query."
            return "\n\n---\n\n".join(results)
        except Exception as e:
            return f"Error searching document: {str(e)}"

    def _run(self, **kwargs) -> str:
        raise NotImplementedError("Async only.")