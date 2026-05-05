from fastapi import APIRouter, Depends, status
from sqlmodel.ext.asyncio.session import AsyncSession
from src.db.session import get_db_session as get_session
from src.app.schemas.meeting_schema import MeetingUpdateSchema, MeetingCreateSchema
from src.app.services.meeting_service import MeetingService
from src.app.dependencies.bearer import AccessTokenBearer, RoleChecker
from fastapi.exceptions import HTTPException
from typing import Optional

service = MeetingService()
meeting_router = APIRouter()


@meeting_router.get("/")
async def list_meetings(
    client_phone: Optional[str] = None,
    meeting_status: Optional[str] = None,
    offset: int = 0,
    limit: int = 20,
    token_data: dict = Depends(AccessTokenBearer()),
    session: AsyncSession = Depends(get_session),
):
    meetings = await service.list_meetings(session, client_phone, meeting_status, offset, limit)
    return [m.model_dump() for m in meetings]


@meeting_router.get("/{meeting_id}")
async def get_meeting(
    meeting_id: str,
    token_data: dict = Depends(AccessTokenBearer()),
    session: AsyncSession = Depends(get_session),
):
    meeting = await service.get_meeting(meeting_id, session)
    if not meeting:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")
    return meeting.model_dump()

@meeting_router.get("/{meeting_id}/details")
async def get_meeting_details(
    meeting_id: str,
    token_data: dict = Depends(AccessTokenBearer()),
    session: AsyncSession = Depends(get_session),
):
    meeting_details = await service.get_meeting_details(meeting_id, session)
    if not meeting_details:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")
    return meeting_details


@meeting_router.post("/", status_code=status.HTTP_201_CREATED)
async def create_meeting(
    data: MeetingCreateSchema,
    token_data: dict = Depends(AccessTokenBearer()),
    session: AsyncSession = Depends(get_session),
):
    meeting = await service.create_meeting(data, session)
    return meeting.model_dump()


@meeting_router.put("/{meeting_id}")
async def update_meeting(
    meeting_id: str,
    data: MeetingUpdateSchema,
    token_data: dict = Depends(AccessTokenBearer()),
    session: AsyncSession = Depends(get_session),
):
    meeting = await service.update_meeting(meeting_id, data, session)
    if not meeting:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")
    return meeting.model_dump()


@meeting_router.delete("/{meeting_id}")
async def cancel_meeting(
    meeting_id: str,
    reason: str = "Cancelled by admin",
    token_data: dict = Depends(AccessTokenBearer()),
    session: AsyncSession = Depends(get_session),
):
    meeting = await service.cancel_meeting(meeting_id, reason, session)
    if not meeting:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")
    return {"message": "Meeting cancelled", "meeting": meeting.model_dump()}
