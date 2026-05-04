from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from src.app.models.company_document import CompanyDocument, CompanyDocType
from src.agent.modules.memory.chroma_client import get_collection
from src.agent.modules.memory.long_term_company_memory import (
    store_company_chunk,
    delete_company_document,
)
from datetime import datetime
from typing import Optional, List
import uuid


COLLECTION_NAME = "company_knowledge"


class DocumentService:
    """
    Handles company document upload, ChromaDB ingestion (via LangChain),
    and metadata storage in the company_documents table.
    """

    async def list_documents(
        self,
        session: AsyncSession,
        doc_type: Optional[str] = None,
        active_only: bool = True,
        offset: int = 0,
        limit: int = 20,
    ):
        statement = select(CompanyDocument)
        if active_only:
            statement = statement.where(CompanyDocument.is_active == True)
        if doc_type:
            statement = statement.where(CompanyDocument.doc_type == doc_type)
        statement = statement.order_by(CompanyDocument.ingested_at.desc())
        statement = statement.offset(offset).limit(limit)
        result = await session.exec(statement)
        return result.all()

    async def get_document(self, doc_id: str, session: AsyncSession):
        statement = select(CompanyDocument).where(CompanyDocument.doc_id == doc_id)
        result = await session.exec(statement)
        return result.first()

    async def upload_documents(
        self,
        files: List[tuple[str, bytes]],  # list of (filename, content_bytes)
        doc_type: str,
        session: AsyncSession,
    ) -> List[CompanyDocument]:
        """
        Process one or more files:
        1. Use LangChain document loaders to extract text (PDF / DOCX / TXT)
        2. Chunk the text with RecursiveCharacterTextSplitter
        3. Store chunks in ChromaDB via the existing LangChain Chroma wrapper
        4. Store metadata in company_documents table
        """
        from langchain.text_splitter import RecursiveCharacterTextSplitter

        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        results: List[CompanyDocument] = []

        for filename, file_content in files:
            doc_id = f"doc_{uuid.uuid4().hex[:12]}"

            # Extract text using LangChain loaders
            text = self._load_text(filename, file_content)

            # Chunk text
            chunks = splitter.split_text(text)

            # Store each chunk in ChromaDB via the existing helper
            for i, chunk_text in enumerate(chunks):
                store_company_chunk(
                    doc_id=doc_id,
                    chunk_index=i,
                    text=chunk_text,
                    doc_type=doc_type,
                    filename=filename,
                )

            # Persist metadata in DB
            token_count = sum(len(c.split()) for c in chunks)
            doc = CompanyDocument(
                doc_id=doc_id,
                filename=filename,
                doc_type=doc_type,
                chunk_count=len(chunks),
                token_count=token_count,
                ingested_at=datetime.now(),
                last_updated_at=datetime.now(),
                is_active=True,
            )
            session.add(doc)
            results.append(doc)

        await session.commit()
        for doc in results:
            await session.refresh(doc)
        return results

    async def delete_document(self, doc_id: str, session: AsyncSession):
        """Soft-delete: set is_active=False and remove from ChromaDB."""
        doc = await self.get_document(doc_id, session)
        if not doc:
            return False

        # Remove from ChromaDB via the existing helper
        try:
            delete_company_document(doc_id)
        except Exception:
            pass  # best-effort

        doc.is_active = False
        session.add(doc)
        await session.commit()
        return True

    # ─── Text extraction via LangChain loaders ────────────────────────────

    def _load_text(self, filename: str, content: bytes) -> str:
        """Parse raw bytes in memory using Langchain parsers."""
        from langchain_core.document_loaders import Blob
        
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "txt"
        blob = Blob(data=content)
        
        if ext == "pdf":
            from langchain_community.document_loaders.parsers.pdf import PyMuPDFParser
            parser = PyMuPDFParser()
        elif ext in ("docx", "doc"):
            from langchain_community.document_loaders.parsers.msword import MsWordParser
            parser = MsWordParser()
        else:
            from langchain_community.document_loaders.parsers.txt import TextParser
            parser = TextParser()

        docs = list(parser.lazy_parse(blob))
        return "\n\n".join(d.page_content for d in docs)
