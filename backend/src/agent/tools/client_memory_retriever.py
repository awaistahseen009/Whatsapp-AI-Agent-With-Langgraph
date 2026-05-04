# app/tools/client_memory_retriever.py

from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type
from src.agent.modules.memory.long_term_client_memory import search_client_memories


class ClientMemoryInput(BaseModel):
    query: str = Field(description="Query to search this client's long term memory")
    phone_number: str = Field(description="Client's WhatsApp phone number")


class ClientMemoryRetriever(BaseTool):
    name: str = "client_memory_retriever"
    description: str = (
        "Search long term memory for this specific client. "
        "Call this when the client references something from a past conversation "
        "that is not present in the current 20 messages — past preferences, "
        "properties they rejected, budget they mentioned, personal details they shared. "
        "Always search here before asking the client to repeat themselves."
    )
    args_schema: Type[BaseModel] = ClientMemoryInput

    async def _arun(self, query: str, phone_number: str) -> str:
        try:
            results = search_client_memories(
                phone_number=phone_number,
                query=query,
                k=6
            )

            if not results:
                return "No relevant memories found for this client."

            return "\n\n---\n\n".join(results)

        except Exception as e:
            return f"Error retrieving client memories: {str(e)}"

    def _run(self, **kwargs) -> str:
        raise NotImplementedError("Async only.")