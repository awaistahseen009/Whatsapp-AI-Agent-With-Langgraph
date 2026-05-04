from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type, Optional
from datetime import datetime
import pytz
from src.db.session import get_async_session
from src.app.models.meeting import Meeting, MeetingType, MeetingStatus


class MeetingLoggerInput(BaseModel):
    client_phone: str = Field(description="Client's WhatsApp phone number")
    meeting_type: str = Field(description="virtual_consultation, property_tour, document_signing, followup")
    meeting_format: str = Field(description="'virtual' or 'in_person'")
    start_time: str = Field(description="ISO 8601 datetime in UTC. Example: 2025-04-26T11:00:00+00:00")
    end_time: str = Field(description="ISO 8601 datetime in UTC")
    client_timezone: str = Field(description="Client's IANA timezone for display")
    duration_minutes: int = Field(description="Duration in minutes")
    zoom_meeting_id: Optional[str] = Field(default=None, description="Zoom meeting ID if virtual")
    zoom_join_url: Optional[str] = Field(default=None, description="Zoom join URL if virtual")
    calendar_event_id: Optional[str] = Field(default=None, description="Google Calendar event ID")
    notes: Optional[str] = Field(default=None, description="Any additional notes")


class MeetingLogger(BaseTool):
    name: str = "meeting_logger"
    description: str = (
        "Logs a meeting to the internal database after it has been created in Zoom or Google Calendar. "
        "Always call this immediately after zoom_create_meeting or calendar_create_event succeeds. "
        "This is the internal source of truth for all scheduled meetings."
    )
    args_schema: Type[BaseModel] = MeetingLoggerInput

    async def _arun(
        self,
        client_phone: str,
        meeting_type: str,
        meeting_format: str,
        start_time: str,
        end_time: str,
        client_timezone: str,
        duration_minutes: int,
        zoom_meeting_id: Optional[str] = None,
        zoom_join_url: Optional[str] = None,
        calendar_event_id: Optional[str] = None,
        notes: Optional[str] = None
    ) -> str:
        try:
            async with get_async_session() as session:
                meeting = Meeting(
                    client_phone=client_phone,
                    meeting_type=MeetingType(meeting_type),
                    meeting_format=meeting_format,
                    start_time=datetime.fromisoformat(start_time),
                    end_time=datetime.fromisoformat(end_time),
                    client_timezone=client_timezone,
                    duration_minutes=duration_minutes,
                    zoom_meeting_id=zoom_meeting_id,
                    zoom_join_url=zoom_join_url,
                    calendar_event_id=calendar_event_id,
                    notes=notes,
                    status=MeetingStatus.SCHEDULED,
                    created_at=datetime.now()
                )
                session.add(meeting)
                await session.commit()
                await session.refresh(meeting)

                return (
                    f"Meeting logged successfully.\n"
                    f"Internal Meeting ID: {meeting.meeting_id}\n"
                    f"Type: {meeting.meeting_type.value}\n"
                    f"Start: {meeting.start_time}"
                )

        except Exception as e:
            return f"Error logging meeting: {str(e)}"

    def _run(self, **kwargs) -> str:
        raise NotImplementedError("Async only.")