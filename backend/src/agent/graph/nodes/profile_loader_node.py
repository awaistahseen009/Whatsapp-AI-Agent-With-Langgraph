from sqlmodel import select
from src.agent.state import AgentState
from src.db.session import get_async_session
from src.app.models.client import Client
import re


EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")


def _extract_email_from_latest_message(state: AgentState) -> str | None:
    messages = state.get("messages") or []
    if not messages:
        return None
    content = getattr(messages[-1], "content", "") or ""
    match = EMAIL_PATTERN.search(content)
    return match.group(0).strip().lower() if match else None


async def profile_loader_node(state: AgentState) -> dict:
    """
    Loads client profile from PostgreSQL into state.
    Only queries DB if profile fields are missing.
    On every subsequent message checkpointer already restores them — guard passes,
    returns empty dict, zero DB calls.
    """
    phone = state["client_phone"]
    email_from_message = _extract_email_from_latest_message(state)

    if (
        state.get("onboarding_complete")
        and state.get("client_name")
        and state.get("client_timezone")
        and state.get("client_email")
        and not email_from_message
    ):
        return {}

    async with get_async_session() as session:
        result = await session.execute(
            select(Client).where(Client.phone_num == phone)
        )
        client = result.scalar_one_or_none()

        if client and email_from_message and client.email != email_from_message:
            client.email = email_from_message
            session.add(client)
            await session.commit()
            await session.refresh(client)

    if not client:
        async with get_async_session() as session:
            new_client = Client(
                phone_num=phone,
                name="",
                city="",
                timezone="",
                onboarding_complete=False
            )
            session.add(new_client)
            await session.commit()

        return {
            "client_name": "",
            "client_email": "",
            "client_timezone": "",
            "onboarding_complete": False,
        }

    return {
        "client_name": client.name or "",
        "client_email": client.email,
        "client_timezone": client.timezone or "",
        "onboarding_complete": client.onboarding_complete,
    }


def route_after_profile(state: AgentState) -> str:
    if not state.get("onboarding_complete"):
        return "onboarding_decide_node"
    return "memory_retrieval_node"
