from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from src.app.models.client import Client
from src.app.models.client_property_views import ClientPropertyViews
from typing import Optional


class ClientService:
    async def list_clients(
        self,
        session: AsyncSession,
        status: Optional[str] = None,
        city: Optional[str] = None,
        offset: int = 0,
        limit: int = 20,
    ):
        statement = select(Client).order_by(Client.created_at.desc())
        if status:
            statement = statement.where(Client.status == status)
        if city:
            statement = statement.where(Client.city.ilike(f"%{city}%"))
        statement = statement.offset(offset).limit(limit)
        result = await session.exec(statement)
        return result.all()

    async def get_client(self, phone: str, session: AsyncSession):
        statement = select(Client).where(Client.phone_num == phone)
        result = await session.exec(statement)
        return result.first()

    async def get_client_views(self, phone: str, session: AsyncSession):
        statement = select(ClientPropertyViews).where(
            ClientPropertyViews.client_phone == phone
        ).order_by(ClientPropertyViews.viewed_at.desc())
        result = await session.exec(statement)
        return result.all()

    async def get_clients_by_date_range(self, session: AsyncSession, start_date, end_date):
        """Get clients created within a date range"""
        statement = select(Client).where(
            Client.created_at >= start_date,
            Client.created_at <= end_date
        ).order_by(Client.created_at.desc())
        result = await session.exec(statement)
        return result.all()
