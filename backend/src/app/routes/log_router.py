from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession
from src.db.session import get_db_session as get_session
from src.app.services.log_service import LogService
from src.app.dependencies.bearer import RoleChecker
from typing import Optional

service = LogService()
log_router = APIRouter()


@log_router.get("/tokens/")
async def list_token_logs(
    client_phone: Optional[str] = None,
    offset: int = 0,
    limit: int = 50,
    token_data: dict = Depends(RoleChecker(["owner"])),
    session: AsyncSession = Depends(get_session),
):
    logs = await service.list_token_logs(session, client_phone, offset, limit)
    return [l.model_dump() for l in logs]


@log_router.get("/tools/")
async def list_tool_logs(
    client_phone: Optional[str] = None,
    tool_name: Optional[str] = None,
    success: Optional[bool] = None,
    offset: int = 0,
    limit: int = 50,
    token_data: dict = Depends(RoleChecker(["owner"])),
    session: AsyncSession = Depends(get_session),
):
    logs = await service.list_tool_logs(session, client_phone, tool_name, success, offset, limit)
    return [l.model_dump() for l in logs]


@log_router.get("/errors/")
async def list_error_logs(
    client_phone: Optional[str] = None,
    offset: int = 0,
    limit: int = 50,
    token_data: dict = Depends(RoleChecker(["owner"])),
    session: AsyncSession = Depends(get_session),
):
    logs = await service.list_error_logs(session, client_phone, offset, limit)
    return [l.model_dump() for l in logs]
