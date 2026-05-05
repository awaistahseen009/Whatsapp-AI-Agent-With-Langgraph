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


@client_router.get("/stats/monthly")
async def get_monthly_client_stats(
    session: AsyncSession = Depends(get_session),
    token_data: dict = Depends(AccessTokenBearer()),
):
    """Get client stats for current and previous month"""
    from datetime import datetime, timedelta
    now = datetime.utcnow()
    current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_month_start = (current_month_start - timedelta(days=32)).replace(day=1)
    last_month_end = current_month_start - timedelta(microseconds=1)
    
    current_clients = await service.get_clients_by_date_range(session, current_month_start, now)
    last_month_clients = await service.get_clients_by_date_range(session, last_month_start, last_month_end)
    
    current_converted = [c for c in current_clients if c.status.value == 'converted']
    last_month_converted = [c for c in last_month_clients if c.status.value == 'converted']
    
    return {
        "current_month": {
            "total_clients": len(current_clients),
            "converted_clients": len(current_converted),
            "conversion_rate": len(current_clients) > 0 and (len(current_converted) / len(current_clients) * 100) or 0
        },
        "last_month": {
            "total_clients": len(last_month_clients),
            "converted_clients": len(last_month_converted),
            "conversion_rate": len(last_month_clients) > 0 and (len(last_month_converted) / len(last_month_clients) * 100) or 0
        }
    }
