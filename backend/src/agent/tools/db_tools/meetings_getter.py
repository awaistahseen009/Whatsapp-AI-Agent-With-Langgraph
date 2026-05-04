from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type, Optional
from sqlmodel import select
from sqlalchemy import and_
from src.db.session import get_async_session
from src.app.models.meeting import Meeting, MeetingStatus
import pytz


class MeetingsGetterInput(BaseModel):
    client_phone: str = Field(description="Client's WhatsApp phone number")
    status: Optional[str] = Field(default=None, description="Filter by status: scheduled, completed, cancelled, no_show")
    client_timezone: Optional[str] = Field(default=None, description="IANA timezone to display times in")


class MeetingsGetter(BaseTool):
    name: str = "meetings_getter"
    description: str = (
        "Retrieves meetings for a specific client from the internal database. "
        "Use this when client asks about upcoming or past appointments. "
        "Faster than calling Zoom or Calendar APIs."
    )
    args_schema: Type[BaseModel] = MeetingsGetterInput

    async def _arun(
        self,
        client_phone: str,
        status: Optional[str] = None,
        client_timezone: Optional[str] = None
    ) -> str:
        try:
            async with get_async_session() as session:
                filters = [Meeting.client_phone == client_phone]
                if status:
                    filters.append(Meeting.status == MeetingStatus(status))

                result = await session.execute(
                    select(Meeting)
                    .where(and_(*filters))
                    .order_by(Meeting.start_time.asc())
                )
                meetings = result.scalars().all()

                if not meetings:
                    return "No meetings found for this client."

                display_tz = pytz.timezone(client_timezone) if client_timezone else pytz.utc

                output = f"Found {len(meetings)} meeting(s):\n\n"
                for m in meetings:
                    local_start = m.start_time.astimezone(display_tz)
                    local_end = m.end_time.astimezone(display_tz)
                    output += (
                        f"Internal ID: {m.meeting_id}\n"
                        f"Type: {m.meeting_type.value}\n"
                        f"Status: {m.status.value}\n"
                        f"Start: {local_start.strftime('%B %d, %Y at %I:%M %p')}\n"
                        f"End: {local_end.strftime('%I:%M %p')}\n"
                        f"Duration: {m.duration_minutes} minutes\n"
                        f"Zoom URL: {m.zoom_join_url or 'N/A'}\n"
                        f"Notes: {m.notes or 'N/A'}\n"
                        f"{'─' * 40}\n"
                    )
                return output

        except Exception as e:
            return f"Error retrieving meetings: {str(e)}"

    def _run(self, **kwargs) -> str:
        raise NotImplementedError("Async only.")