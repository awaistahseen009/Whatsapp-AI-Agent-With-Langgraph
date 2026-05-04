from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type
from sqlmodel import select
from sqlalchemy.orm import joinedload
from src.db.session import get_async_session
from src.app.models.client_property_views import ClientPropertyViews
from src.app.models.property import Property


class ViewedPropertiesGetterInput(BaseModel):
    phone_number: str = Field(description="Client's WhatsApp phone number")


class ViewedPropertiesGetter(BaseTool):
    name: str = "viewed_properties_getter"
    description: str = (
        "Returns all properties a client has already been shown. "
        "Call this before making new property recommendations "
        "to avoid showing properties the client has already seen."
    )
    args_schema: Type[BaseModel] = ViewedPropertiesGetterInput

    async def _arun(self, phone_number: str) -> str:
        try:
            async with get_async_session() as session:
                result = await session.execute(
                    select(ClientPropertyViews, Property)
                    .join(Property, ClientPropertyViews.property_id == Property.property_id)
                    .where(ClientPropertyViews.client_phone == phone_number)
                    .order_by(ClientPropertyViews.viewed_at.desc())
                )
                rows = result.all()

                if not rows:
                    return "This client has not been shown any properties yet."

                output = f"Properties already shown to client ({len(rows)} total):\n\n"
                for view, prop in rows:
                    output += (
                        f"Property: {prop.title}\n"
                        f"Location: {prop.location_area}, {prop.location_city}\n"
                        f"Price: ${prop.price:,}\n"
                        f"Viewed At: {view.viewed_at.strftime('%B %d, %Y at %I:%M %p')}\n"
                        f"Feedback: {view.client_feedback or 'None'}\n"
                        f"{'─' * 40}\n"
                    )
                return output

        except Exception as e:
            return f"Error retrieving viewed properties: {str(e)}"

    def _run(self, **kwargs) -> str:
        raise NotImplementedError("Async only.")