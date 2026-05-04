from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type
from sqlmodel import select
from src.db.session import get_async_session
from src.app.models.client import Client


class ClientProfileReaderInput(BaseModel):
    phone_number: str = Field(description="Client's WhatsApp phone number")


class ClientProfileReader(BaseTool):
    name: str = "client_profile_reader"
    description: str = (
        "Reads the full client profile from the database. "
        "Call this to check client status, email, budget, preferred locations, "
        "loan approval status, intent, or any structured field. "
        "Always call this at the start of a session if client details are needed."
    )
    args_schema: Type[BaseModel] = ClientProfileReaderInput

    @staticmethod
    def _format_budget(value: int | None) -> str:
        if value is None:
            return "N/A"
        if value <= 0:
            return "Flexible / not provided"
        return str(value)

    async def _arun(self, phone_number: str) -> str:
        try:
            async with get_async_session() as session:
                result = await session.execute(
                    select(Client).where(Client.phone_num == phone_number)
                )
                client = result.scalar_one_or_none()

                if not client:
                    return f"No client found with phone number {phone_number}."

                return (
                    f"Phone: {client.phone_num}\n"
                    f"Name: {client.name}\n"
                    f"Email: {client.email or 'N/A'}\n"
                    f"City: {client.city}\n"
                    f"Timezone: {client.timezone}\n"
                    f"Status: {client.status.value}\n"
                    f"Intent: {client.intent.value if client.intent else 'N/A'}\n"
                    f"Budget Min: {self._format_budget(client.budget_min)}\n"
                    f"Budget Max: {self._format_budget(client.budget_max)}\n"
                    f"Preferred Locations: {', '.join(client.preferred_locations) if client.preferred_locations else 'N/A'}\n"
                    f"Property Type Preference: {', '.join(client.property_type_pref) if client.property_type_pref else 'N/A'}\n"
                    f"Loan Pre-approved: {client.loan_preapproved}\n"
                    f"Onboarding Complete: {client.onboarding_complete}\n"
                    f"Created At: {client.created_at}\n"
                    f"Last Active: {client.last_active_at}"
                )
        except Exception as e:
            return f"Error reading client profile: {str(e)}"

    def _run(self, **kwargs) -> str:
        raise NotImplementedError("Async only.")
