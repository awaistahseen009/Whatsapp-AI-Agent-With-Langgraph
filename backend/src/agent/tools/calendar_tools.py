# app/tools/calendar_event.py

import asyncio
from functools import partial
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type, Optional, Literal
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import pytz
from config import Config
import re


# ─── Shared Service ───────────────────────────────────────────────────────────

def get_calendar_service():
    credentials_info = {
        "type": "service_account",
        "project_id": Config.GOOGLE_PROJECT_ID,
        "private_key_id": Config.GOOGLE_PRIVATE_KEY_ID,
        "private_key": Config.GOOGLE_PRIVATE_KEY.replace("\\n", "\n"),
        "client_email": Config.GOOGLE_CLIENT_EMAIL,
        "client_id": Config.GOOGLE_CLIENT_ID,
        "token_uri": Config.GOOGLE_TOKEN_URI,
    }

    credentials = service_account.Credentials.from_service_account_info(
        credentials_info,
        scopes=["https://www.googleapis.com/auth/calendar"]
    )

    # Direct service account access — client gets a universal "Add to Calendar" link
    return build("calendar", "v3", credentials=credentials)


EMAIL_PATTERN = re.compile(r"^[\w.+-]+@[\w-]+(?:\.[\w-]+)+$")


def normalize_email(email: Optional[str]) -> Optional[str]:
    if not email:
        return None
    email = email.strip().lower()
    return email if EMAIL_PATTERN.match(email) else None


def normalize_emails(emails: Optional[list[str]]) -> list[str]:
    if not emails:
        return []
    normalized = []
    for email in emails:
        value = normalize_email(email)
        if value and value not in normalized:
            normalized.append(value)
    return normalized


def localize_to_utc(datetime_str: str, timezone_str: str) -> datetime:
    tz = pytz.timezone(timezone_str)
    local_dt = datetime.fromisoformat(datetime_str)
    if local_dt.tzinfo is None:
        local_dt = tz.localize(local_dt)
    return local_dt.astimezone(pytz.utc)


# ─── Create Event ─────────────────────────────────────────────────────────────

class CalendarCreateInput(BaseModel):
    title: str = Field(description="Event title")
    start_datetime: str = Field(description="ISO 8601 datetime in client's local time. Example: 2025-04-26T15:00:00")
    client_timezone: str = Field(description="IANA timezone from timezone_resolver. Example: America/Toronto")
    duration_minutes: int = Field(default=30, description="Duration in minutes")
    client_email: Optional[str] = Field(default=None, description="Client email if known")
    allow_without_client_email: bool = Field(
        default=False,
        description="Set true only if the client explicitly declined to provide an email"
    )
    additional_attendees: Optional[list[str]] = Field(
        default=None,
        description="Any additional attendee emails"
    )
    description: str = Field(default="", description="Event notes")
    location: Optional[str] = Field(default=None, description="Physical location or address")
    reminder_minutes: int = Field(default=60, description="Email reminder before event in minutes")
    popup_reminder_minutes: int = Field(default=15, description="Popup reminder before event in minutes")
    check_availability: bool = Field(
        default=True,
        description="Check if slot is free before creating. Set False to force-create."
    )
    color_id: Optional[str] = Field(
        default=None,
        description="Google Calendar color ID 1-11. 1=Lavender 2=Sage 3=Grape 4=Flamingo 5=Banana 6=Tangerine 7=Peacock 8=Graphite 9=Blueberry 10=Basil 11=Tomato"
    )


class CalendarEventCreator(BaseTool):
    name: str = "calendar_create_event"
    description: str = (
        "Creates a Google Calendar event. "
        "By default checks slot availability first and blocks if taken. "
        "Call timezone_resolver first if client_timezone is not known."
    )
    args_schema: Type[BaseModel] = CalendarCreateInput

    def _run_sync(
        self,
        title: str,
        start_datetime: str,
        client_timezone: str,
        duration_minutes: int,
        client_email: Optional[str],
        allow_without_client_email: bool,
        additional_attendees: Optional[list],
        description: str,
        location: Optional[str],
        reminder_minutes: int,
        popup_reminder_minutes: int,
        check_availability: bool,
        color_id: Optional[str]
    ) -> str:
        try:
            client_email = normalize_email(client_email)
            additional_attendees = normalize_emails(additional_attendees)
            if not client_email and not allow_without_client_email:
                return (
                    "Client email is required before creating a calendar event. "
                    "Ask the client for their email, or set allow_without_client_email=true only if they explicitly declined."
                )

            try:
                tz = pytz.timezone(client_timezone)
            except pytz.exceptions.UnknownTimeZoneError:
                return f"Invalid timezone '{client_timezone}'. Call timezone_resolver again."

            start_utc = localize_to_utc(start_datetime, client_timezone)
            end_utc = start_utc + timedelta(minutes=duration_minutes)
            service = get_calendar_service()

            if check_availability:
                freebusy = service.freebusy().query(body={
                    "timeMin": start_utc.isoformat(),
                    "timeMax": end_utc.isoformat(),
                    "timeZone": "UTC",
                    "items": [{"id": Config.GOOGLE_CALENDAR_ID}]
                }).execute()
                busy = freebusy["calendars"][Config.GOOGLE_CALENDAR_ID]["busy"]
                if busy:
                    local_start = start_utc.astimezone(tz)
                    return (
                        f"Slot at {local_start.strftime('%B %d, %Y at %I:%M %p')} "
                        f"({client_timezone}) is already booked. "
                        f"Suggest an alternative time to the client."
                    )

            attendees = []
            if client_email:
                attendees.append({"email": client_email})
            if additional_attendees:
                for email in additional_attendees:
                    attendees.append({"email": email})

            body = {
                "summary": title,
                "description": description,
                "start": {"dateTime": start_utc.isoformat(), "timeZone": "UTC"},
                "end": {"dateTime": end_utc.isoformat(), "timeZone": "UTC"},
                "attendees": attendees,
                "reminders": {
                    "useDefault": False,
                    "overrides": [
                        {"method": "email", "minutes": reminder_minutes},
                        {"method": "popup", "minutes": popup_reminder_minutes}
                    ]
                }
            }
            if location:
                body["location"] = location
            if color_id:
                body["colorId"] = color_id

            event = service.events().insert(
                calendarId=Config.GOOGLE_CALENDAR_ID,
                body=body,
                sendUpdates="all"
            ).execute()

            local_start = start_utc.astimezone(tz)
            local_end = end_utc.astimezone(tz)

            # Build a universal "Add to Calendar" link any client can use
            gcal_start = start_utc.strftime("%Y%m%dT%H%M%SZ")
            gcal_end = end_utc.strftime("%Y%m%dT%H%M%SZ")
            from urllib.parse import quote
            gcal_link = (
                f"https://calendar.google.com/calendar/render?action=TEMPLATE"
                f"&text={quote(title)}"
                f"&dates={gcal_start}/{gcal_end}"
                f"&details={quote(description or '')}"
                f"&location={quote(location or '')}"
            )

            return (
                f"Event created.\n"
                f"Event ID: {event['id']}\n"
                f"Title: {event['summary']}\n"
                f"Time: {local_start.strftime('%B %d, %Y at %I:%M %p')} "
                f"to {local_end.strftime('%I:%M %p')} ({client_timezone})\n"
                f"Attendees: {', '.join(a['email'] for a in attendees) if attendees else 'None'}\n"
                f"Location: {location or 'N/A'}\n"
                f"Add to Calendar: {gcal_link}"
            )
        except Exception as e:
            return f"Error: {str(e)}"

    async def _arun(self, **kwargs) -> str:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, partial(self._run_sync, **kwargs))

    def _run(self, **kwargs) -> str:
        raise NotImplementedError("Async only.")


# ─── Get Event ────────────────────────────────────────────────────────────────

class CalendarGetInput(BaseModel):
    event_id: str = Field(description="Google Calendar event ID")
    client_timezone: Optional[str] = Field(
        default=None,
        description="IANA timezone to display times in. Falls back to UTC if not provided"
    )


class CalendarEventGetter(BaseTool):
    name: str = "calendar_get_event"
    description: str = "Retrieves full details of a specific calendar event by its ID."
    args_schema: Type[BaseModel] = CalendarGetInput

    def _run_sync(self, event_id: str, client_timezone: Optional[str]) -> str:
        try:
            service = get_calendar_service()
            event = service.events().get(
                calendarId=Config.GOOGLE_CALENDAR_ID,
                eventId=event_id
            ).execute()

            start_raw = event["start"].get("dateTime", event["start"].get("date"))
            end_raw = event["end"].get("dateTime", event["end"].get("date"))

            if client_timezone and start_raw:
                try:
                    tz = pytz.timezone(client_timezone)
                    start_dt = datetime.fromisoformat(start_raw).astimezone(tz)
                    end_dt = datetime.fromisoformat(end_raw).astimezone(tz)
                    start_display = start_dt.strftime("%B %d, %Y at %I:%M %p") + f" ({client_timezone})"
                    end_display = end_dt.strftime("%I:%M %p")
                except Exception:
                    start_display = start_raw
                    end_display = end_raw
            else:
                start_display = start_raw
                end_display = end_raw

            attendees = [
                f"{a.get('displayName', a['email'])} ({'accepted' if a.get('responseStatus') == 'accepted' else a.get('responseStatus', 'unknown')})"
                for a in event.get("attendees", [])
            ]

            return (
                f"Event ID: {event['id']}\n"
                f"Title: {event['summary']}\n"
                f"Start: {start_display}\n"
                f"End: {end_display}\n"
                f"Location: {event.get('location', 'N/A')}\n"
                f"Description: {event.get('description', 'N/A')}\n"
                f"Attendees: {', '.join(attendees) if attendees else 'None'}\n"
                f"Status: {event.get('status', 'N/A')}\n"
                f"Link: {event.get('htmlLink', 'N/A')}"
            )
        except Exception as e:
            return f"Error: {str(e)}"

    async def _arun(self, **kwargs) -> str:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, partial(self._run_sync, **kwargs))

    def _run(self, **kwargs) -> str:
        raise NotImplementedError("Async only.")


# ─── List Events ──────────────────────────────────────────────────────────────

class CalendarListInput(BaseModel):
    from_datetime: Optional[str] = Field(
        default=None,
        description="List events from this datetime onwards. ISO 8601. Example: 2025-04-26T00:00:00Z. Defaults to now if not provided."
    )
    to_datetime: Optional[str] = Field(
        default=None,
        description="List events up to this datetime. ISO 8601. Example: 2025-05-10T23:59:59Z. Open-ended if not provided."
    )
    client_timezone: Optional[str] = Field(
        default=None,
        description="IANA timezone to display event times in. Falls back to UTC if not provided."
    )
    max_results: int = Field(default=10, description="Max events to return, up to 250")
    search_query: Optional[str] = Field(
        default=None,
        description="Free text search within event titles and descriptions"
    )
    order_by: Literal["startTime", "updated"] = Field(
        default="startTime",
        description="Sort order: startTime or updated"
    )
    show_deleted: bool = Field(default=False, description="Include deleted/cancelled events")
    next_page_token: Optional[str] = Field(
        default=None,
        description="Token from previous list response to fetch next page"
    )


class CalendarEventLister(BaseTool):
    name: str = "calendar_list_events"
    description: str = (
        "Lists calendar events with full filtering control. "
        "Filter by date range, search by keyword, paginate results. "
        "Use from_datetime to list from a specific date onwards. "
        "Leave to_datetime empty for open-ended listing."
    )
    args_schema: Type[BaseModel] = CalendarListInput

    def _run_sync(
        self,
        from_datetime: Optional[str],
        to_datetime: Optional[str],
        client_timezone: Optional[str],
        max_results: int,
        search_query: Optional[str],
        order_by: str,
        show_deleted: bool,
        next_page_token: Optional[str]
    ) -> str:
        try:
            service = get_calendar_service()

            params = {
                "calendarId": Config.GOOGLE_CALENDAR_ID,
                "maxResults": min(max_results, 250),
                "singleEvents": True,
                "orderBy": order_by,
                "showDeleted": show_deleted
            }

            if from_datetime:
                params["timeMin"] = from_datetime
            else:
                params["timeMin"] = datetime.utcnow().isoformat() + "Z"

            if to_datetime:
                params["timeMax"] = to_datetime
            if search_query:
                params["q"] = search_query
            if next_page_token:
                params["pageToken"] = next_page_token

            result = service.events().list(**params).execute()
            events = result.get("items", [])

            if not events:
                return "No events found for the given filters."

            display_tz = pytz.timezone(client_timezone) if client_timezone else pytz.utc

            output = f"Total returned: {len(events)}\n"
            if result.get("nextPageToken"):
                output += f"Next page token: {result['nextPageToken']}\n"
            output += "\n"

            for e in events:
                start_raw = e["start"].get("dateTime", e["start"].get("date"))
                end_raw = e["end"].get("dateTime", e["end"].get("date"))

                try:
                    start_display = datetime.fromisoformat(start_raw).astimezone(display_tz).strftime("%B %d, %Y at %I:%M %p")
                    end_display = datetime.fromisoformat(end_raw).astimezone(display_tz).strftime("%I:%M %p")
                except Exception:
                    start_display = start_raw
                    end_display = end_raw

                attendees = [a["email"] for a in e.get("attendees", [])]
                output += (
                    f"ID: {e['id']}\n"
                    f"Title: {e.get('summary', 'N/A')}\n"
                    f"Start: {start_display}\n"
                    f"End: {end_display}\n"
                    f"Location: {e.get('location', 'N/A')}\n"
                    f"Attendees: {', '.join(attendees) if attendees else 'None'}\n"
                    f"Status: {e.get('status', 'N/A')}\n"
                    f"{'─' * 40}\n"
                )
            return output

        except Exception as e:
            return f"Error: {str(e)}"

    async def _arun(self, **kwargs) -> str:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, partial(self._run_sync, **kwargs))

    def _run(self, **kwargs) -> str:
        raise NotImplementedError("Async only.")


# ─── Update Event ─────────────────────────────────────────────────────────────

class CalendarUpdateInput(BaseModel):
    event_id: str = Field(description="Google Calendar event ID to update")
    title: Optional[str] = Field(default=None, description="New event title")
    start_datetime: Optional[str] = Field(
        default=None,
        description="New start time in ISO 8601 in client's local time"
    )
    client_timezone: Optional[str] = Field(
        default=None,
        description="IANA timezone from timezone_resolver. Required if updating start_datetime."
    )
    duration_minutes: Optional[int] = Field(default=None, description="New duration in minutes")
    description: Optional[str] = Field(default=None, description="Updated event notes")
    location: Optional[str] = Field(default=None, description="Updated physical location")
    add_attendees: Optional[list[str]] = Field(
        default=None,
        description="Attendee emails to add"
    )
    remove_attendees: Optional[list[str]] = Field(
        default=None,
        description="Attendee emails to remove"
    )
    reminder_minutes: Optional[int] = Field(default=None, description="Updated email reminder in minutes")
    color_id: Optional[str] = Field(default=None, description="Updated Google Calendar color ID 1-11")
    check_availability: bool = Field(
        default=True,
        description="Check new slot availability before updating time"
    )


class CalendarEventUpdater(BaseTool):
    name: str = "calendar_update_event"
    description: str = (
        "Updates an existing calendar event. "
        "Only pass fields that need to change. "
        "If updating start_datetime, client_timezone is required — call timezone_resolver first. "
        "Can add or remove specific attendees without replacing the full list."
    )
    args_schema: Type[BaseModel] = CalendarUpdateInput

    def _run_sync(
        self,
        event_id: str,
        title: Optional[str],
        start_datetime: Optional[str],
        client_timezone: Optional[str],
        duration_minutes: Optional[int],
        description: Optional[str],
        location: Optional[str],
        add_attendees: Optional[list],
        remove_attendees: Optional[list],
        reminder_minutes: Optional[int],
        color_id: Optional[str],
        check_availability: bool
    ) -> str:
        try:
            service = get_calendar_service()
            event = service.events().get(
                calendarId=Config.GOOGLE_CALENDAR_ID,
                eventId=event_id
            ).execute()

            if title is not None:
                event["summary"] = title
            if description is not None:
                event["description"] = description
            if location is not None:
                event["location"] = location
            if color_id is not None:
                event["colorId"] = color_id

            if start_datetime is not None:
                if not client_timezone:
                    return "client_timezone required when updating start_datetime. Call timezone_resolver first."
                try:
                    pytz.timezone(client_timezone)
                except pytz.exceptions.UnknownTimeZoneError:
                    return f"Invalid timezone '{client_timezone}'. Call timezone_resolver again."

                start_utc = localize_to_utc(start_datetime, client_timezone)
                dur = duration_minutes or 30
                end_utc = start_utc + timedelta(minutes=dur)

                if check_availability:
                    freebusy = service.freebusy().query(body={
                        "timeMin": start_utc.isoformat(),
                        "timeMax": end_utc.isoformat(),
                        "timeZone": "UTC",
                        "items": [{"id": Config.GOOGLE_CALENDAR_ID}]
                    }).execute()
                    busy = freebusy["calendars"][Config.GOOGLE_CALENDAR_ID]["busy"]
                    busy = [b for b in busy if b.get("eventId") != event_id]
                    if busy:
                        tz = pytz.timezone(client_timezone)
                        local_start = start_utc.astimezone(tz)
                        return (
                            f"New slot at {local_start.strftime('%B %d, %Y at %I:%M %p')} "
                            f"({client_timezone}) is already booked. "
                            f"Suggest an alternative time to the client."
                        )

                event["start"] = {"dateTime": start_utc.isoformat(), "timeZone": "UTC"}
                event["end"] = {"dateTime": end_utc.isoformat(), "timeZone": "UTC"}

            elif duration_minutes is not None:
                current_start = event["start"].get("dateTime")
                if current_start:
                    start_utc = datetime.fromisoformat(current_start).astimezone(pytz.utc)
                    end_utc = start_utc + timedelta(minutes=duration_minutes)
                    event["end"] = {"dateTime": end_utc.isoformat(), "timeZone": "UTC"}

            existing = {a["email"]: a for a in event.get("attendees", [])}
            if add_attendees:
                for email in add_attendees:
                    if email not in existing:
                        existing[email] = {"email": email}
            if remove_attendees:
                for email in remove_attendees:
                    existing.pop(email, None)
            event["attendees"] = list(existing.values())

            if reminder_minutes is not None:
                event["reminders"] = {
                    "useDefault": False,
                    "overrides": [
                        {"method": "email", "minutes": reminder_minutes},
                        {"method": "popup", "minutes": 15}
                    ]
                }

            updated = service.events().update(
                calendarId=Config.GOOGLE_CALENDAR_ID,
                eventId=event_id,
                body=event,
                sendUpdates="all"
            ).execute()

            return (
                f"Event updated.\n"
                f"Event ID: {updated['id']}\n"
                f"Title: {updated['summary']}\n"
                f"Start: {updated['start'].get('dateTime', 'N/A')}\n"
                f"Link: {updated.get('htmlLink', 'N/A')}"
            )
        except Exception as e:
            return f"Error: {str(e)}"

    async def _arun(self, **kwargs) -> str:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, partial(self._run_sync, **kwargs))

    def _run(self, **kwargs) -> str:
        raise NotImplementedError("Async only.")


# ─── Delete Event ─────────────────────────────────────────────────────────────

class CalendarDeleteInput(BaseModel):
    event_id: str = Field(description="Google Calendar event ID to delete")
    notify_attendees: Literal["all", "externalOnly", "none"] = Field(
        default="all",
        description="Who to notify: all, externalOnly, or none"
    )


class CalendarEventDeleter(BaseTool):
    name: str = "calendar_delete_event"
    description: str = (
        "Permanently deletes a calendar event. "
        "Only call after client explicitly confirms cancellation."
    )
    args_schema: Type[BaseModel] = CalendarDeleteInput

    def _run_sync(self, event_id: str, notify_attendees: str) -> str:
        try:
            service = get_calendar_service()
            service.events().delete(
                calendarId=Config.GOOGLE_CALENDAR_ID,
                eventId=event_id,
                sendUpdates=notify_attendees
            ).execute()
            return f"Event {event_id} deleted successfully."
        except Exception as e:
            return f"Error: {str(e)}"

    async def _arun(self, **kwargs) -> str:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, partial(self._run_sync, **kwargs))

    def _run(self, **kwargs) -> str:
        raise NotImplementedError("Async only.")
