from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type, Optional
from datetime import datetime
from sqlmodel import select
from src.db.session import get_async_session
from src.app.models.client import Client, ClientStatus, ClientIntent


class ClientProfileUpdaterInput(BaseModel):
    phone_number: str = Field(description="Client's WhatsApp phone number")
    name: Optional[str] = Field(default=None, description="Client full name")
    email: Optional[str] = Field(default=None, description="Client email address")
    city: Optional[str] = Field(default=None, description="Client city")
    timezone: Optional[str] = Field(default=None, description="Client IANA timezone")
    status: Optional[str] = Field(default=None, description="new, serious, converted, lost")
    intent: Optional[str] = Field(default=None, description="buy, invest, rent")
    budget_min: Optional[int] = Field(default=None, description="Minimum budget")
    budget_max: Optional[int] = Field(default=None, description="Maximum budget")
    preferred_locations: Optional[list[str]] = Field(default=None, description="List of preferred locations")
    property_type_pref: Optional[list[str]] = Field(default=None, description="List of preferred property types")
    loan_preapproved: Optional[bool] = Field(default=None, description="Whether client has loan pre-approval")
    onboarding_complete: Optional[bool] = Field(default=None, description="Whether onboarding is complete")


class ClientProfileUpdater(BaseTool):
    name: str = "client_profile_updater"
    description: str = (
        "Updates specific fields on the client's profile. "
        "Only pass fields that need to change. "
        "Call this when client shares email, updates budget, changes intent, "
        "confirms loan pre-approval, or when their status changes."
    )
    args_schema: Type[BaseModel] = ClientProfileUpdaterInput

    async def _arun(
        self,
        phone_number: str,
        name: Optional[str] = None,
        email: Optional[str] = None,
        city: Optional[str] = None,
        timezone: Optional[str] = None,
        status: Optional[str] = None,
        intent: Optional[str] = None,
        budget_min: Optional[int] = None,
        budget_max: Optional[int] = None,
        preferred_locations: Optional[list] = None,
        property_type_pref: Optional[list] = None,
        loan_preapproved: Optional[bool] = None,
        onboarding_complete: Optional[bool] = None
    ) -> str:
        try:
            async with get_async_session() as session:
                result = await session.execute(
                    select(Client).where(Client.phone_num == phone_number)
                )
                client = result.scalar_one_or_none()

                if not client:
                    return f"No client found with phone number {phone_number}."

                if name is not None:
                    client.name = name
                if email is not None:
                    client.email = email
                if city is not None:
                    client.city = city
                if timezone is not None:
                    client.timezone = timezone
                if status is not None:
                    client.status = ClientStatus(status)
                if intent is not None:
                    client.intent = ClientIntent(intent)
                if budget_min is not None and budget_min > 0:
                    client.budget_min = budget_min
                if budget_max is not None and budget_max > 0:
                    client.budget_max = budget_max
                if preferred_locations is not None:
                    client.preferred_locations = preferred_locations
                if property_type_pref is not None:
                    client.property_type_pref = property_type_pref
                if loan_preapproved is not None:
                    client.loan_preapproved = loan_preapproved
                if onboarding_complete is not None:
                    client.onboarding_complete = onboarding_complete

                client.last_active_at = datetime.utcnow()

                session.add(client)
                await session.commit()

                return f"Client profile for {phone_number} updated successfully."

        except Exception as e:
            return f"Error updating client profile: {str(e)}"

    def _run(self, **kwargs) -> str:
        raise NotImplementedError("Async only.")
