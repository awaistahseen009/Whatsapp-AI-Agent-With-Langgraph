from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type, Optional
from datetime import datetime
from sqlmodel import select
from src.db.session import get_async_session
from src.app.models.meeting import Meeting, MeetingStatus
import uuid


class MeetingStatusUpdaterInput(BaseModel):
    meeting_id: str = Field(description="Internal meeting UUID from the database")
    status: str = Field(description="New status: completed, cancelled, no_show")
    cancellation_reason: Optional[str] = Field(default=None, description="Required if status is cancelled")


class MeetingStatusUpdater(BaseTool):
    name: str = "meeting_status_updater"
    description: str = (
        "Updates the status of a meeting in the database. "
        "Call this after cancelling a meeting in Zoom or Calendar, "
        "or when marking a meeting as completed or no_show."
    )
    args_schema: Type[BaseModel] = MeetingStatusUpdaterInput

    async def _arun(
        self,
        meeting_id: str,
        status: str,
        cancellation_reason: Optional[str] = None
    ) -> str:
        try:
            async with get_async_session() as session:
                result = await session.execute(
                    select(Meeting).where(Meeting.meeting_id == uuid.UUID(meeting_id))
                )
                meeting = result.scalar_one_or_none()

                if not meeting:
                    return f"No meeting found with ID {meeting_id}."

                meeting.status = MeetingStatus(status)

                if status == "cancelled":
                    meeting.cancelled_at = datetime.now()
                    meeting.cancellation_reason = cancellation_reason

                session.add(meeting)
                await session.commit()

                return f"Meeting {meeting_id} status updated to {status}."

        except Exception as e:
            return f"Error updating meeting status: {str(e)}"

    def _run(self, **kwargs) -> str:
        raise NotImplementedError("Async only.")