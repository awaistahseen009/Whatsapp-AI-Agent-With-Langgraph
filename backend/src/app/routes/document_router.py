from fastapi import APIRouter, Depends, status, UploadFile, File, Form
from sqlmodel.ext.asyncio.session import AsyncSession
from src.db.session import get_db_session as get_session
from src.app.services.document_service import DocumentService
from src.app.dependencies.bearer import AccessTokenBearer, RoleChecker
from fastapi.exceptions import HTTPException
from typing import Optional, List

service = DocumentService()
document_router = APIRouter()


@document_router.get("/")
async def list_documents(
    doc_type: Optional[str] = None,
    active_only: bool = True,
    offset: int = 0,
    limit: int = 20,
    token_data: dict = Depends(AccessTokenBearer()),
    session: AsyncSession = Depends(get_session),
):
    docs = await service.list_documents(session, doc_type, active_only, offset, limit)
    return [d.model_dump() for d in docs]


@document_router.get("/{doc_id}")
async def get_document(
    doc_id: str,
    token_data: dict = Depends(AccessTokenBearer()),
    session: AsyncSession = Depends(get_session),
):
    doc = await service.get_document(doc_id, session)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return doc.model_dump()


@document_router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_documents(
    doc_type: str = Form(..., description="property_listing, area_guide, policy, faq, developer_profile, legal"),
    files: List[UploadFile] = File(..., description="One or more files (PDF, DOCX, TXT)"),
    token_data: dict = Depends(RoleChecker(["owner"])),
    session: AsyncSession = Depends(get_session),
):
    """Upload one or multiple documents. Supports PDF, DOCX, and TXT."""
    file_tuples = []
    for f in files:
        content = await f.read()
        file_tuples.append((f.filename, content))

    docs = await service.upload_documents(file_tuples, doc_type, session)
    return [d.model_dump() for d in docs]


@document_router.delete("/{doc_id}")
async def delete_document(
    doc_id: str,
    token_data: dict = Depends(RoleChecker(["owner"])),
    session: AsyncSession = Depends(get_session),
):
    deleted = await service.delete_document(doc_id, session)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return {"message": "Document deleted successfully"}
