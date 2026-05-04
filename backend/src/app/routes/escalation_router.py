from fastapi import APIRouter, Depends, status
from sqlmodel.ext.asyncio.session import AsyncSession
from src.db.session import get_db_session as get_session
from src.app.schemas.escalation_schema import EscalationResolveSchema
from src.app.services.escalation_service import EscalationService
from src.app.dependencies.bearer import AccessTokenBearer, RoleChecker
from fastapi.exceptions import HTTPException
from typing import Optional

service = EscalationService()
escalation_router = APIRouter()


@escalation_router.get("/")
async def list_escalations(
    escalation_status: Optional[str] = None,
    client_phone: Optional[str] = None,
    offset: int = 0,
    limit: int = 20,
    token_data: dict = Depends(AccessTokenBearer()),
    session: AsyncSession = Depends(get_session),
):
    escalations = await service.list_escalations(session, escalation_status, client_phone, offset, limit)
    return [e.model_dump() for e in escalations]


@escalation_router.get("/{escalation_id}")
async def get_escalation(
    escalation_id: str,
    token_data: dict = Depends(AccessTokenBearer()),
    session: AsyncSession = Depends(get_session),
):
    esc = await service.get_escalation(escalation_id, session)
    if not esc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Escalation not found")
    return esc.model_dump()


@escalation_router.put("/{escalation_id}/resolve")
async def resolve_escalation(
    escalation_id: str,
    data: EscalationResolveSchema,
    token_data: dict = Depends(RoleChecker(["owner"])),
    session: AsyncSession = Depends(get_session),
):
    esc = await service.resolve_escalation(escalation_id, data, session)
    if not esc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Escalation not found")
    return esc.model_dump()
