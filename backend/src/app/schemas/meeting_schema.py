from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class MeetingCreateSchema(BaseModel):
    client_phone: str = Field(description="Client phone number")
    meeting_type: str = Field(description="virtual_consultation, property_tour, document_signing, followup")
    meeting_format: str = Field(default="virtual", description="virtual or in_person")
    start_time: datetime = Field(description="Meeting start time (ISO 8601)")
    duration_minutes: int = Field(default=30, gt=0, description="Duration in minutes")
    client_timezone: str = Field(default="America/New_York", description="Client timezone")
    notes: Optional[str] = Field(default=None, description="Meeting notes")
    zoom_meeting_id: Optional[str] = None
    zoom_join_url: Optional[str] = None


class MeetingUpdateSchema(BaseModel):
    status: Optional[str] = Field(default=None, description="scheduled, completed, cancelled, no_show")
    notes: Optional[str] = None
    cancellation_reason: Optional[str] = None
