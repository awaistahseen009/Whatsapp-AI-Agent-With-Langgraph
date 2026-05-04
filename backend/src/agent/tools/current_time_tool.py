from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type
from datetime import datetime
import pytz
from config import Config

class CurrentTimeInput(BaseModel):
    # Dummy field because LangChain tools usually need at least one argument
    # Some older versions complain if args_schema requires nothing, but we can make it optional
    timezone: str = Field(
        default=Config.AGENT_TIMEZONE, 
        description="Optional: Request time in a specific timezone. Defaults to Agent's business timezone."
    )

class CurrentTimeTool(BaseTool):
    name: str = "get_current_time"
    description: str = (
        "Gets the current date and time dynamically. "
        "Useful for knowing what 'today' is before proposing or booking meetings, "
        "and verifying the current time in the business timezone."
    )
    args_schema: Type[BaseModel] = CurrentTimeInput

    def _run(self, timezone: str = Config.AGENT_TIMEZONE) -> str:
        try:
            tz = pytz.timezone(timezone)
            now = datetime.now(tz)
            date_str = now.strftime("%A, %B %d, %Y")
            time_str = now.strftime("%I:%M %p")
            return f"The current date is {date_str} and the time is {time_str} in {timezone} timezone."
        except Exception as e:
            # Fallback to UTC if invalid timezone passed
            now = datetime.now(pytz.utc)
            return f"Invalid timezone '{timezone}'. Current UTC time is: {now.strftime('%A, %B %d, %Y %I:%M %p')}."

    async def _arun(self, timezone: str = Config.AGENT_TIMEZONE) -> str:
        return self._run(timezone)
