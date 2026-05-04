from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from src.app.models.meeting import Meeting, MeetingStatus
from src.app.schemas.meeting_schema import MeetingUpdateSchema, MeetingCreateSchema
from typing import Optional
from datetime import datetime, timedelta


class MeetingService:
    async def create_meeting(self, data: MeetingCreateSchema, session: AsyncSession):
        end_time = data.start_time + timedelta(minutes=data.duration_minutes)
        meeting = Meeting(
            client_phone=data.client_phone,
            meeting_type=data.meeting_type,
            meeting_format=data.meeting_format,
            start_time=data.start_time,
            end_time=end_time,
            duration_minutes=data.duration_minutes,
            client_timezone=data.client_timezone,
            notes=data.notes,
            zoom_meeting_id=data.zoom_meeting_id,
            zoom_join_url=data.zoom_join_url,
            status=MeetingStatus.SCHEDULED,
        )
        session.add(meeting)
        await session.commit()
        await session.refresh(meeting)
        return meeting

    async def list_meetings(
        self,
        session: AsyncSession,
        client_phone: Optional[str] = None,
        status: Optional[str] = None,
        offset: int = 0,
        limit: int = 20,
    ):
        statement = select(Meeting).order_by(Meeting.start_time.desc())
        if client_phone:
            statement = statement.where(Meeting.client_phone == client_phone)
        if status:
            statement = statement.where(Meeting.status == status)
        statement = statement.offset(offset).limit(limit)
        result = await session.exec(statement)
        return result.all()

    async def get_meeting(self, meeting_id: str, session: AsyncSession):
        statement = select(Meeting).where(Meeting.meeting_id == meeting_id)
        result = await session.exec(statement)
        return result.first()

    async def update_meeting(self, meeting_id: str, data: MeetingUpdateSchema, session: AsyncSession):
        meeting = await self.get_meeting(meeting_id, session)
        if not meeting:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(meeting, key, value)
        if data.status == "cancelled":
            meeting.cancelled_at = datetime.now()
        session.add(meeting)
        await session.commit()
        await session.refresh(meeting)
        return meeting

    async def cancel_meeting(self, meeting_id: str, reason: str, session: AsyncSession):
        meeting = await self.get_meeting(meeting_id, session)
        if not meeting:
            return None
        meeting.status = MeetingStatus.CANCELLED
        meeting.cancelled_at = datetime.now()
        meeting.cancellation_reason = reason
        session.add(meeting)
        await session.commit()
        await session.refresh(meeting)
        return meeting
