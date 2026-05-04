from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from src.app.models.escalation import Escalation, EscalationStatus
from src.app.schemas.escalation_schema import EscalationResolveSchema
from typing import Optional
from datetime import datetime


class EscalationService:
    async def list_escalations(
        self,
        session: AsyncSession,
        status: Optional[str] = None,
        client_phone: Optional[str] = None,
        offset: int = 0,
        limit: int = 20,
    ):
        statement = select(Escalation).order_by(Escalation.triggered_at.desc())
        if status:
            statement = statement.where(Escalation.status == status)
        if client_phone:
            statement = statement.where(Escalation.client_phone == client_phone)
        statement = statement.offset(offset).limit(limit)
        result = await session.exec(statement)
        return result.all()

    async def get_escalation(self, escalation_id: str, session: AsyncSession):
        statement = select(Escalation).where(Escalation.escalation_id == escalation_id)
        result = await session.exec(statement)
        return result.first()

    async def resolve_escalation(self, escalation_id: str, data: EscalationResolveSchema, session: AsyncSession):
        esc = await self.get_escalation(escalation_id, session)
        if not esc:
            return None
        if data.status == "resolved":
            esc.status = EscalationStatus.RESOLVED
        elif data.status == "dismissed":
            esc.status = EscalationStatus.DISMISSED
        esc.resolved_at = datetime.now()
        esc.resolution_notes = data.resolution_notes
        session.add(esc)
        await session.commit()
        await session.refresh(esc)
        return esc
