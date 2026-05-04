from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type
from datetime import datetime
import pytz

class BusinessHoursInput(BaseModel):
    proposed_datetime: str = Field(
        description="The proposed date and time in the client's timezone (ISO 8601). Example: 2025-04-26T14:00:00"
    )
    client_timezone: str = Field(
        description="The client's IANA timezone string. Example: America/New_York"
    )

class BusinessHoursTool(BaseTool):
    name: str = "validate_business_hours"
    description: str = (
        "Validates if a proposed meeting time falls within Riley Estate's business hours "
        "(Monday to Friday, 9:00 AM to 7:00 PM Asia/Karachi time). "
        "ALWAYS call this tool to check ANY time proposed by either you or the client BEFORE confirming that time."
    )
    args_schema: Type[BaseModel] = BusinessHoursInput

    def _run(self, proposed_datetime: str, client_timezone: str) -> str:
        try:
            # 1. Localize the proposed time to the client's timezone
            client_tz = pytz.timezone(client_timezone)
            # Remove any trailing Z or offset if they passed it, to cleanly localize
            clean_dt_str = proposed_datetime.split("+")[0].split("Z")[0]
            client_dt = datetime.fromisoformat(clean_dt_str)
            if client_dt.tzinfo is None:
                client_dt = client_tz.localize(client_dt)
                
            # 2. Convert to Riley Estate's timezone (Asia/Karachi)
            riley_tz = pytz.timezone("Asia/Karachi")
            riley_dt = client_dt.astimezone(riley_tz)
            
            # 3. Check business hours
            is_weekend = riley_dt.weekday() >= 5  # 5 = Saturday, 6 = Sunday
            hour = riley_dt.hour
            minute = riley_dt.minute
            
            # Office hours: 9:00 AM to 7:00 PM (19:00)
            # Must be >= 9:00 and < 19:00 (since 19:30 is closed)
            # Oh wait, 19:00 is exactly 7 PM. So if hour < 9 or (hour >= 19 and minute > 0) or hour > 19 -> bad
            # Actually, if the meeting is 30 mins, 18:30 is the last slot. Let's just say strictly < 19:00 for start time.
            is_within_hours = (9 <= hour < 19)
            
            client_display = client_dt.strftime("%A, %B %d at %I:%M %p")
            riley_display = riley_dt.strftime("%A, %B %d at %I:%M %p PKT")
            
            if is_weekend:
                return (
                    f"REJECTED: The proposed time ({client_display} {client_timezone}) is {riley_display}. "
                    "Riley Estate is CLOSED on weekends. DO NOT confirm this time. "
                    "Tell the client it's a weekend for our office and suggest a weekday slot."
                )
            
            if not is_within_hours:
                return (
                    f"REJECTED: The proposed time ({client_display} {client_timezone}) is {riley_display}. "
                    "This is OUTSIDE our business hours (Monday-Friday 9AM-7PM PKT). DO NOT confirm this time. "
                    "Tell the client it falls outside business hours and suggest nearby valid times."
                )
                
            return (
                f"APPROVED: The proposed time ({client_display} {client_timezone}) is {riley_display}. "
                "This is WITHIN business hours. You may proceed to confirm this time with the client."
            )
            
        except Exception as e:
            return f"Error validating time: {str(e)}. Make sure to pass a valid ISO 8601 string."

    async def _arun(self, proposed_datetime: str, client_timezone: str) -> str:
        # tool is entirely synchronous/CPU-bound, so just call _run directly
        return self._run(proposed_datetime, client_timezone)
