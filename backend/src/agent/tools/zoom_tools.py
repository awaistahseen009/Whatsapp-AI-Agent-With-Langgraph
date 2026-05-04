# app/tools/zoom_meeting.py

import httpx
import time
import base64
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type, Optional, Literal
from datetime import datetime
import pytz
from config import Config
import re


# ─── Shared Auth ─────────────────────────────────────────────────────────────

_zoom_token_cache = {
    "access_token": None,
    "expires_at": 0
}

EMAIL_PATTERN = re.compile(r"^[\w.+-]+@[\w-]+(?:\.[\w-]+)+$")


def normalize_email(email: Optional[str]) -> Optional[str]:
    if not email:
        return None
    email = email.strip().lower()
    return email if EMAIL_PATTERN.match(email) else None

async def get_zoom_token() -> str:
    now = time.time()

    if _zoom_token_cache["access_token"] and now < _zoom_token_cache["expires_at"] - 60:
        return _zoom_token_cache["access_token"]

    credentials = f"{Config.ZOOM_CLIENT_ID}:{Config.ZOOM_CLIENT_SECRET}"
    encoded = base64.b64encode(credentials.encode()).decode()

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://zoom.us/oauth/token",
            params={
                "grant_type": "account_credentials",
                "account_id": Config.ZOOM_ACCOUNT_ID
            },
            headers={"Authorization": f"Basic {encoded}"}
        )

    if response.status_code != 200:
        raise ValueError(f"Zoom token fetch failed: {response.text}")

    data = response.json()
    _zoom_token_cache["access_token"] = data["access_token"]
    _zoom_token_cache["expires_at"] = now + data["expires_in"]

    return _zoom_token_cache["access_token"]


def localize_zoom_datetime(start_time: str, client_timezone: str):
    tz = pytz.timezone(client_timezone)
    local_dt = datetime.fromisoformat(start_time)
    if local_dt.tzinfo is None:
        local_dt = tz.localize(local_dt)
    return local_dt


# ─── Create Meeting ───────────────────────────────────────────────────────────

class ZoomCreateInput(BaseModel):
    topic: str = Field(description="Meeting topic")
    start_time: str = Field(description="ISO 8601 datetime in client's local time. Example: 2025-04-26T15:00:00")
    client_timezone: str = Field(description="IANA timezone from timezone_resolver. Example: Asia/Dubai")
    duration: int = Field(default=30, description="Duration in minutes")
    client_email: Optional[str] = Field(default=None, description="Client's email for the meeting invite")
    allow_without_client_email: bool = Field(
        default=False,
        description="Set true only if the client explicitly declined to provide an email"
    )
    agenda: str = Field(default="", description="Optional agenda")
    password: Optional[str] = Field(default=None, description="Optional meeting password")
    join_before_host: bool = Field(default=True, description="Allow participants to join before host")
    waiting_room: bool = Field(default=False, description="Enable waiting room")
    auto_recording: Literal["none", "local", "cloud"] = Field(
        default="none", description="Recording mode: none, local, or cloud"
    )


class ZoomMeetingCreator(BaseTool):
    name: str = "zoom_create_meeting"
    description: str = (
        "Creates a scheduled Zoom meeting. "
        "Call timezone_resolver first if client_timezone is not known. "
        "Only call after client confirms a specific date and time."
    )
    args_schema: Type[BaseModel] = ZoomCreateInput

    async def _arun(
        self,
        topic: str,
        start_time: str,
        client_timezone: str,
        duration: int = 30,
        client_email: Optional[str] = None,
        allow_without_client_email: bool = False,
        agenda: str = "",
        password: Optional[str] = None,
        join_before_host: bool = True,
        waiting_room: bool = False,
        auto_recording: str = "none"
    ) -> str:
        try:
            client_email = normalize_email(client_email)
            if not client_email and not allow_without_client_email:
                return (
                    "Client email is required before creating a Zoom meeting. "
                    "Ask the client for their email, or set allow_without_client_email=true only if they explicitly declined."
                )

            try:
                local_dt = localize_zoom_datetime(start_time, client_timezone)
            except pytz.exceptions.UnknownTimeZoneError:
                return f"Invalid timezone '{client_timezone}'. Call timezone_resolver again."

            zoom_start = local_dt.strftime("%Y-%m-%dT%H:%M:%S")
            token = await get_zoom_token()

            settings = {
                "join_before_host": join_before_host,
                "waiting_room": waiting_room,
                "auto_recording": auto_recording
            }
            if client_email:
                settings["meeting_invitees"] = [{"email": client_email}]
                settings["registrants_email_notification"] = True

            payload = {
                "topic": topic,
                "type": 2,
                "start_time": zoom_start,
                "duration": duration,
                "agenda": agenda,
                "timezone": client_timezone,
                "settings": settings
            }
            if password:
                payload["password"] = password

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.zoom.us/v2/users/me/meetings",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json"
                    },
                    json=payload
                )

            if response.status_code != 201:
                return f"Failed to create meeting: {response.text}"

            data = response.json()
            return (
                f"Meeting created.\n"
                f"Meeting ID: {data['id']}\n"
                f"Join URL: {data['join_url']}\n"
                f"Invitee Email: {client_email or 'None'}\n"
                f"Start: {zoom_start} ({client_timezone})\n"
                f"Duration: {data['duration']} minutes\n"
                f"Password: {data.get('password', 'None')}"
            )
        except Exception as e:
            return f"Error: {str(e)}"

    def _run(self, **kwargs) -> str:
        raise NotImplementedError("Async only.")


# ─── Get Meeting ──────────────────────────────────────────────────────────────

class ZoomGetInput(BaseModel):
    meeting_id: str = Field(description="Zoom meeting ID")
    show_previous_occurrences: bool = Field(
        default=False,
        description="For recurring meetings, include previous occurrences"
    )


class ZoomMeetingGetter(BaseTool):
    name: str = "zoom_get_meeting"
    description: str = "Retrieves full details of a specific Zoom meeting by its ID."
    args_schema: Type[BaseModel] = ZoomGetInput

    async def _arun(
        self,
        meeting_id: str,
        show_previous_occurrences: bool = False
    ) -> str:
        try:
            token = await get_zoom_token()
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://api.zoom.us/v2/meetings/{meeting_id}",
                    headers={"Authorization": f"Bearer {token}"},
                    params={"show_previous_occurrences": show_previous_occurrences}
                )

            if response.status_code == 404:
                return f"Meeting {meeting_id} not found."
            if response.status_code != 200:
                return f"Failed to get meeting: {response.text}"

            data = response.json()
            return (
                f"Meeting ID: {data['id']}\n"
                f"Topic: {data['topic']}\n"
                f"Status: {data.get('status', 'N/A')}\n"
                f"Start: {data['start_time']} ({data['timezone']})\n"
                f"Duration: {data['duration']} minutes\n"
                f"Agenda: {data.get('agenda', 'N/A')}\n"
                f"Join URL: {data['join_url']}\n"
                f"Password: {data.get('password', 'None')}\n"
                f"Host Email: {data.get('host_email', 'N/A')}"
            )
        except Exception as e:
            return f"Error: {str(e)}"

    def _run(self, **kwargs) -> str:
        raise NotImplementedError("Async only.")


# ─── List Meetings ────────────────────────────────────────────────────────────

class ZoomListInput(BaseModel):
    meeting_type: Literal["scheduled", "live", "upcoming", "upcoming_meetings", "previous_meetings"] = Field(
        default="upcoming",
        description="Filter by type: scheduled, live, upcoming, upcoming_meetings, previous_meetings"
    )
    from_date: Optional[str] = Field(
        default=None,
        description="Filter meetings from this date onwards. ISO 8601 date. Example: 2025-04-26"
    )
    to_date: Optional[str] = Field(
        default=None,
        description="Filter meetings up to this date. ISO 8601 date. Example: 2025-05-10"
    )
    page_size: int = Field(default=10, description="Number of meetings to return, max 300")
    next_page_token: Optional[str] = Field(
        default=None,
        description="Token for fetching the next page of results from a previous list call"
    )


class ZoomMeetingLister(BaseTool):
    name: str = "zoom_list_meetings"
    description: str = (
        "Lists Zoom meetings. "
        "Filter by type, date range, or paginate through results. "
        "Use from_date to list meetings from a specific date onwards. "
        "Use next_page_token from previous response to get more results."
    )
    args_schema: Type[BaseModel] = ZoomListInput

    async def _arun(
        self,
        meeting_type: str = "upcoming",
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        page_size: int = 10,
        next_page_token: Optional[str] = None
    ) -> str:
        try:
            token = await get_zoom_token()

            params = {
                "type": meeting_type,
                "page_size": min(page_size, 300)
            }
            if from_date:
                params["from"] = from_date
            if to_date:
                params["to"] = to_date
            if next_page_token:
                params["next_page_token"] = next_page_token

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.zoom.us/v2/users/me/meetings",
                    headers={"Authorization": f"Bearer {token}"},
                    params=params
                )

            if response.status_code != 200:
                return f"Failed to list meetings: {response.text}"

            data = response.json()
            meetings = data.get("meetings", [])

            if not meetings:
                return "No meetings found for the given filters."

            result = (
                f"Total meetings: {data.get('total_records', len(meetings))}\n"
                f"Showing: {len(meetings)}\n"
            )
            if data.get("next_page_token"):
                result += f"Next page token: {data['next_page_token']}\n"
            result += "\n"

            for m in meetings:
                result += (
                    f"ID: {m['id']}\n"
                    f"Topic: {m['topic']}\n"
                    f"Start: {m.get('start_time', 'N/A')} ({m.get('timezone', 'N/A')})\n"
                    f"Duration: {m.get('duration', 'N/A')} minutes\n"
                    f"Join URL: {m.get('join_url', 'N/A')}\n"
                    f"{'─' * 40}\n"
                )
            return result

        except Exception as e:
            return f"Error: {str(e)}"

    def _run(self, **kwargs) -> str:
        raise NotImplementedError("Async only.")


# ─── Update Meeting ───────────────────────────────────────────────────────────

class ZoomUpdateInput(BaseModel):
    meeting_id: str = Field(description="Zoom meeting ID to update")
    topic: Optional[str] = Field(default=None, description="New meeting topic")
    start_time: Optional[str] = Field(
        default=None,
        description="New start time in ISO 8601 in client's local time"
    )
    client_timezone: Optional[str] = Field(
        default=None,
        description="IANA timezone from timezone_resolver. Required if updating start_time"
    )
    duration: Optional[int] = Field(default=None, description="New duration in minutes")
    agenda: Optional[str] = Field(default=None, description="New agenda text")
    password: Optional[str] = Field(default=None, description="New meeting password")
    join_before_host: Optional[bool] = Field(default=None, description="Allow join before host")
    waiting_room: Optional[bool] = Field(default=None, description="Enable or disable waiting room")
    auto_recording: Optional[Literal["none", "local", "cloud"]] = Field(
        default=None,
        description="New recording mode"
    )


class ZoomMeetingUpdater(BaseTool):
    name: str = "zoom_update_meeting"
    description: str = (
        "Updates an existing Zoom meeting. "
        "Only pass fields that need to change — everything else stays as-is. "
        "If updating start_time, client_timezone is required — call timezone_resolver first."
    )
    args_schema: Type[BaseModel] = ZoomUpdateInput

    async def _arun(
        self,
        meeting_id: str,
        topic: Optional[str] = None,
        start_time: Optional[str] = None,
        client_timezone: Optional[str] = None,
        duration: Optional[int] = None,
        agenda: Optional[str] = None,
        password: Optional[str] = None,
        join_before_host: Optional[bool] = None,
        waiting_room: Optional[bool] = None,
        auto_recording: Optional[str] = None
    ) -> str:
        try:
            payload = {}
            settings_payload = {}

            if topic is not None:
                payload["topic"] = topic
            if duration is not None:
                payload["duration"] = duration
            if agenda is not None:
                payload["agenda"] = agenda
            if password is not None:
                payload["password"] = password
            if join_before_host is not None:
                settings_payload["join_before_host"] = join_before_host
            if waiting_room is not None:
                settings_payload["waiting_room"] = waiting_room
            if auto_recording is not None:
                settings_payload["auto_recording"] = auto_recording

            if start_time is not None:
                if not client_timezone:
                    return "client_timezone is required when updating start_time. Call timezone_resolver first."
                try:
                    local_dt = localize_zoom_datetime(start_time, client_timezone)
                except pytz.exceptions.UnknownTimeZoneError:
                    return f"Invalid timezone '{client_timezone}'. Call timezone_resolver again."
                payload["start_time"] = local_dt.strftime("%Y-%m-%dT%H:%M:%S")
                payload["timezone"] = client_timezone

            if settings_payload:
                payload["settings"] = settings_payload

            if not payload:
                return "No fields provided to update."

            token = await get_zoom_token()
            async with httpx.AsyncClient() as client:
                response = await client.patch(
                    f"https://api.zoom.us/v2/meetings/{meeting_id}",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json"
                    },
                    json=payload
                )

            if response.status_code == 204:
                return f"Meeting {meeting_id} updated successfully."
            if response.status_code == 404:
                return f"Meeting {meeting_id} not found."
            return f"Failed to update: {response.text}"

        except Exception as e:
            return f"Error: {str(e)}"

    def _run(self, **kwargs) -> str:
        raise NotImplementedError("Async only.")


# ─── Delete Meeting ───────────────────────────────────────────────────────────

class ZoomDeleteInput(BaseModel):
    meeting_id: str = Field(description="Zoom meeting ID to delete")
    notify_registrants: bool = Field(
        default=True,
        description="Send cancellation email to registered participants"
    )
    cancel_meeting_reminder: bool = Field(
        default=True,
        description="Send cancellation reminder to host and panelists"
    )


class ZoomMeetingDeleter(BaseTool):
    name: str = "zoom_delete_meeting"
    description: str = (
        "Permanently deletes a Zoom meeting. "
        "Only call after client explicitly confirms cancellation."
    )
    args_schema: Type[BaseModel] = ZoomDeleteInput

    async def _arun(
        self,
        meeting_id: str,
        notify_registrants: bool = True,
        cancel_meeting_reminder: bool = True
    ) -> str:
        try:
            token = await get_zoom_token()
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"https://api.zoom.us/v2/meetings/{meeting_id}",
                    headers={"Authorization": f"Bearer {token}"},
                    params={
                        "notify_registrants": notify_registrants,
                        "cancel_meeting_reminder": cancel_meeting_reminder
                    }
                )

            if response.status_code == 204:
                return f"Meeting {meeting_id} deleted successfully."
            if response.status_code == 404:
                return f"Meeting {meeting_id} not found."
            return f"Failed to delete: {response.text}"

        except Exception as e:
            return f"Error: {str(e)}"

    def _run(self, **kwargs) -> str:
        raise NotImplementedError("Async only.")
