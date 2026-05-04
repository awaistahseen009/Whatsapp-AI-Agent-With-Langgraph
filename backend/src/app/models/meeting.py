from sqlmodel import SQLModel, Field, Column, ForeignKey
import sqlalchemy.dialects.postgresql as pg
from enum import Enum
from datetime import datetime
import uuid
from sqlalchemy import Enum as SAEnum

from typing import Optional

class MeetingType(str, Enum):
    VIRTUAL_CONSULTATION = "virtual_consultation"
    PROPERTY_TOUR = "property_tour"
    DOCUMENT_SIGNING = "document_signing"
    FOLLOWUP = "followup"

class MeetingStatus(str, Enum):
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"

class Meeting(SQLModel, table=True):
    __tablename__ = "meetings"

    meeting_id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(pg.UUID(as_uuid=True), primary_key=True, nullable=False)
    )
    client_phone: str = Field(sa_column=Column(pg.VARCHAR, ForeignKey("client.phone_num"), nullable=False))
    meeting_type: MeetingType = Field(
        sa_column=Column(SAEnum(MeetingType, name = "meetingtype"), nullable=False)
    )
    meeting_format: str = Field(
        default="virtual",
        sa_column=Column(pg.VARCHAR, nullable=False, server_default="virtual")
    )
    zoom_meeting_id: Optional[str] = Field(sa_column=Column(pg.VARCHAR, nullable=True))
    zoom_join_url: Optional[str] = Field(sa_column=Column(pg.VARCHAR, nullable=True))
    calendar_event_id: Optional[str] = Field(sa_column=Column(pg.VARCHAR, nullable=True))
    
    start_time: datetime = Field(sa_column=Column(pg.TIMESTAMP(timezone=True), nullable=False))
    end_time: datetime = Field(sa_column=Column(pg.TIMESTAMP(timezone=True), nullable=False))
    client_timezone: str = Field(sa_column=Column(pg.VARCHAR, nullable=False))
    duration_minutes: int = Field(sa_column=Column(pg.INTEGER, nullable=False))
    
    status: MeetingStatus = Field(
        sa_column=Column(SAEnum(MeetingStatus, name = "meetingstatus"), nullable=False, default=MeetingStatus.SCHEDULED)
    )
    notes: Optional[str] = Field(sa_column=Column(pg.TEXT, nullable=True))
    created_at: datetime = Field(
        sa_column=Column(pg.TIMESTAMP(timezone=True), nullable=False, default=datetime.now)
    )
    cancelled_at: Optional[datetime] = Field(sa_column=Column(pg.TIMESTAMP(timezone=True), nullable=True))
    cancellation_reason: Optional[str] = Field(sa_column=Column(pg.TEXT, nullable=True))