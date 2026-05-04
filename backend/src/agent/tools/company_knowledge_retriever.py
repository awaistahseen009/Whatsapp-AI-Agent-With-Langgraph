from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type
from src.agent.modules.memory.long_term_company_memory import search_company_knowledge


class CompanyKnowledgeInput(BaseModel):
    query: str = Field(description="Query to search company knowledge base")


class CompanyKnowledgeRetriever(BaseTool):
    name: str = "company_knowledge_retriever"
    description: str = (
        "Search Riley Estate's knowledge base. "
        "Call this before answering any question about the agency, its policies, "
        "commission structure, area guides, developers, property listings, "
        "or the buying and renting process in Florida. "
        "Never answer these questions from memory — always retrieve first."
    )
    args_schema: Type[BaseModel] = CompanyKnowledgeInput

    async def _arun(self, query: str) -> str:
        try:
            results = search_company_knowledge(query=query, k=4)

            if not results:
                return "No relevant information found in the company knowledge base."

            return "\n\n---\n\n".join(results)

        except Exception as e:
            return f"Error retrieving company knowledge: {str(e)}"

    def _run(self, **kwargs) -> str:
        raise NotImplementedError("Async only.")