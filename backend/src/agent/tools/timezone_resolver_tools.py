from langchain.tools import BaseTool
from langchain_groq import ChatGroq
from pydantic import BaseModel, Field
from typing import Type
from config import Config


class TimezoneResolverInput(BaseModel):
    city: str = Field(
        description=(
            "The city or location the client mentioned. "
            "Examples: Dubai, Lahore, London, Sydney, Toronto, Mississauga, Sialkot. "
            "Pass exactly what the client said — do not normalize or guess."
        )
    )


class TimezoneResolverOutput(BaseModel):
    city: str = Field(description="The city name as provided")
    iana_timezone: str = Field(description="IANA timezone string e.g. Asia/Dubai")
    utc_offset: str = Field(description="UTC offset e.g. +05:00")
    timezone_abbreviation: str = Field(description="Timezone abbreviation e.g. PKT, EDT, GMT")


class TimezoneResolver(BaseTool):
    name: str = "timezone_resolver"
    description: str = (
        "Resolves the IANA timezone string for any city in the world. "
        "Always call this first before calling zoom_meeting_creator or calendar_event_registrar "
        "if client_timezone is not already known from the client's onboarding profile. "
        "Returns the exact IANA timezone string to pass to scheduling tools."
    )
    args_schema: Type[BaseModel] = TimezoneResolverInput

    async def _arun(self, city: str) -> str:
        try:
            import json

            llm = ChatGroq(
                model=Config.GROQ_MODEL,
                temperature=0,
                api_key=Config.GROQ_API_KEY
            ).bind(
                response_format={"type": "json_object"}
            )

            schema_hint = json.dumps(TimezoneResolverOutput.model_json_schema(), indent=2)

            messages = [
                (
                    "system",
                    (
                        "You are a strict JSON data processor. "
                        "You MUST respond with ONLY a valid JSON object — no text, no explanation. "
                        "Given any city, town, suburb, or location name in the world, "
                        "return the correct IANA timezone string, UTC offset, and abbreviation. "
                        "You must be accurate — timezone data is used for scheduling real meetings. "
                        "For ambiguous city names that exist in multiple countries, "
                        "use the most populous or commonly referenced one unless context says otherwise. "
                        "Never guess or approximate — return the exact IANA identifier.\n\n"
                        f"Output MUST match this JSON schema:\n{schema_hint}"
                    )
                ),
                (
                    "human",
                    f"Resolve the timezone for this location: {city}"
                )
            ]

            from src.agent.utils.retry import retry_structured_output

            @retry_structured_output(max_attempts=5)
            async def _resolve(msgs):
                response = await llm.ainvoke(msgs)
                return TimezoneResolverOutput.model_validate_json(response.content)

            result: TimezoneResolverOutput = await _resolve(messages)

            return (
                f"City: {result.city}\n"
                f"IANA Timezone: {result.iana_timezone}\n"
                f"UTC Offset: {result.utc_offset}\n"
                f"Abbreviation: {result.timezone_abbreviation}"
            )

        except Exception as e:
            return f"Error resolving timezone for {city}: {str(e)}"

    def _run(self, **kwargs) -> str:
        raise NotImplementedError("This tool is async only. Use graph.ainvoke.")