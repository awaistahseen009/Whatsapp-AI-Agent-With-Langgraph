from fastapi import APIRouter, Depends, status
from sqlmodel.ext.asyncio.session import AsyncSession
from src.db.session import get_db_session as get_session
from src.app.services.client_service import ClientService
from src.app.dependencies.bearer import AccessTokenBearer
from fastapi.exceptions import HTTPException
from typing import Optional

service = ClientService()
client_router = APIRouter()


@client_router.get("/")
async def list_clients(
    client_status: Optional[str] = None,
    city: Optional[str] = None,
    offset: int = 0,
    limit: int = 20,
    token_data: dict = Depends(AccessTokenBearer()),
    session: AsyncSession = Depends(get_session),
):
    clients = await service.list_clients(session, client_status, city, offset, limit)
    return [c.model_dump() for c in clients]


@client_router.get("/{phone}")
async def get_client(
    phone: str,
    token_data: dict = Depends(AccessTokenBearer()),
    session: AsyncSession = Depends(get_session),
):
    client = await service.get_client(phone, session)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
    return client.model_dump()


@client_router.get("/{phone}/views")
async def get_client_views(
    phone: str,
    token_data: dict = Depends(AccessTokenBearer()),
    session: AsyncSession = Depends(get_session),
):
    views = await service.get_client_views(phone, session)
    return [v.model_dump() for v in views]
