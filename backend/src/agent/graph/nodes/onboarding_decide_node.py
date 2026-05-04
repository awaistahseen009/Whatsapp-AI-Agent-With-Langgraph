# src/graph/nodes/onboarding_decide_node.py

from langchain_groq import ChatGroq
from pydantic import BaseModel, Field
from typing import Optional
from sqlmodel import select
from src.agent.state import AgentState
from src.db.session import get_async_session
from src.app.models.client import Client, ClientIntent
from config import Config


# ─── Structured extraction schema ────────────────────────────────────────────

class OnboardingExtraction(BaseModel):
    name: Optional[str] = Field(
        default=None,
        description="Client full name if explicitly mentioned"
    )
    city: Optional[str] = Field(
        default=None,
        description="City or area in Florida if mentioned"
    )
    intent: Optional[str] = Field(
        default=None,
        description="buy, rent, or invest — only if explicitly stated"
    )
    budget_min: Optional[int] = Field(
        default=None,
        description="Minimum budget in USD if mentioned"
    )
    budget_max: Optional[int] = Field(
        default=None,
        description=(
            "Maximum budget in USD if mentioned. "
            "If client says 'not sure', 'flexible', 'I have enough', 'I don't know' — return -1 as a signal."
        )
    )
    timezone: Optional[str] = Field(
        default=None,
        description="Valid IANA timezone string resolved from city. Example: America/New_York for Miami"
    )


# ─── Field skip config ────────────────────────────────────────────────────────

SKIPPABLE_FIELDS = {"budget"}
MAX_ATTEMPTS = 3


def _get_missing(client: Client) -> list[str]:
    """Returns ordered list of fields still empty on the client row."""
    missing = []
    if not client.name:
        missing.append("name")
    if not client.city:
        missing.append("city")
    if not client.intent:
        missing.append("intent")
    if client.budget_min is None and client.budget_max is None:
        missing.append("budget")
    return missing


def _is_skipped(field: str, attempts: dict) -> bool:
    return field in SKIPPABLE_FIELDS and attempts.get(field, 0) >= MAX_ATTEMPTS


def _get_required_missing(client: Client, attempts: dict) -> list[str]:
    return [field for field in _get_missing(client) if not _is_skipped(field, attempts)]


async def onboarding_decide_node(state: AgentState) -> dict:
    """
    Responsibility: extract profile fields from latest message, save to DB,
    update attempt counters, check completion.
    Does NOT generate any reply — llm_node does that with full context.
    """
    phone = state["client_phone"]
    messages = state.get("messages", [])
    last_message = messages[-1].content if messages else ""
    attempts = dict(state.get("onboarding_attempts", {}))

    # ─── Load current client row ──────────────────────────────────────────
    async with get_async_session() as session:
        result = await session.execute(
            select(Client).where(Client.phone_num == phone)
        )
        client = result.scalar_one_or_none()

    if not client:
        return {}

    # ─── Extract answers from latest message ─────────────────────────────
    from src.agent.utils.retry import retry_structured_output
    import json

    extraction_llm = ChatGroq(
        model=Config.GROQ_MODEL,
        temperature=0,
        api_key=Config.GROQ_API_KEY,
    ).bind(
        response_format={"type": "json_object"}
    )

    schema_hint = json.dumps(OnboardingExtraction.model_json_schema(), indent=2)

    @retry_structured_output(max_attempts=5)
    async def _extract(msgs):
        response = await extraction_llm.ainvoke(msgs)
        return OnboardingExtraction.model_validate_json(response.content)

    extraction: OnboardingExtraction = await _extract([
        (
            "system",
            "You are a strict JSON data extraction processor. "
            "You MUST respond with ONLY a valid JSON object — no text, no greetings, no explanation. "
            "Extract onboarding information from the client message below. "
            "Return null for anything not explicitly stated. "
            "For timezone: if a city is mentioned resolve it to a valid IANA timezone string "
            "e.g. America/New_York for Miami, America/Chicago for Tampa. "
            "For budget: parse natural language — 'around 400k' means budget_max=400000, "
            "'between 300k and 500k' means budget_min=300000 budget_max=500000. "
            "If client says 'not sure', 'flexible', 'I have enough', 'I don't know' about budget — return budget_max=-1. "
            "For intent: only accept buy, rent, or invest as values — null otherwise.\n\n"
            f"Output MUST match this JSON schema:\n{schema_hint}"
        ),
        ("human", last_message)
    ])

    # ─── Save extracted fields to DB ─────────────────────────────────────
    async with get_async_session() as session:
        result = await session.execute(
            select(Client).where(Client.phone_num == phone)
        )
        client = result.scalar_one_or_none()

        updated = False
        fields_found = []
        budget_skipped = False

        if extraction.name and not client.name:
            client.name = extraction.name
            updated = True
            fields_found.append("name")

        if extraction.city and not client.city:
            client.city = extraction.city
            updated = True
            fields_found.append("city")

        if extraction.intent and not client.intent:
            try:
                client.intent = ClientIntent(extraction.intent)
                updated = True
                fields_found.append("intent")
            except ValueError:
                pass

        if extraction.timezone and not client.timezone:
            client.timezone = extraction.timezone
            updated = True

        if extraction.budget_max == -1 and client.budget_max is None:
            budget_skipped = True
        else:
            if extraction.budget_min and not client.budget_min:
                client.budget_min = extraction.budget_min
                updated = True
                fields_found.append("budget")
            if extraction.budget_max and extraction.budget_max > 0 and not client.budget_max:
                client.budget_max = extraction.budget_max
                updated = True
                if "budget" not in fields_found:
                    fields_found.append("budget")

        if updated:
            session.add(client)
            await session.commit()
            await session.refresh(client)

    # ─── Update attempt counters ──────────────────────────────────────────
    missing_before = _get_missing(client)

    for field in missing_before:
        if field not in fields_found:
            attempts[field] = attempts.get(field, 0) + 1

    for field in fields_found:
        attempts.pop(field, None)

    if budget_skipped:
        attempts["budget"] = MAX_ATTEMPTS

    # ─── Check completion ─────────────────────────────────────────────────
    required_missing = _get_required_missing(client, attempts)

    if not required_missing:
        async with get_async_session() as session:
            result = await session.execute(
                select(Client).where(Client.phone_num == phone)
            )
            client = result.scalar_one_or_none()
            client.onboarding_complete = True
            session.add(client)
            await session.commit()
            await session.refresh(client)

        return {
            "client_name": client.name,
            "client_timezone": client.timezone or "",
            "onboarding_complete": True,
            "onboarding_attempts": attempts,
            "onboarding_missing_fields": required_missing,
        }

    # ─── Still missing → pass context to llm_node ────────────────────────
    return {
        "client_name": client.name or "",
        "client_timezone": client.timezone or "",
        "onboarding_complete": False,
        "onboarding_attempts": attempts,
        "onboarding_missing_fields": required_missing,   # llm_node reads this to know what to ask
    }


def route_after_onboarding(state: AgentState) -> str:
    if state.get("onboarding_complete"):
        return "memory_retrieval_node"
    return "llm_node"  
