from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type
from datetime import datetime
from src.db.session import get_async_session
from src.app.models.client_property_views import ClientPropertyViews


class PropertyViewLoggerInput(BaseModel):
    phone_number: str = Field(description="Client's WhatsApp phone number")
    property_id: str = Field(description="Property UUID that was shown")
    source: str = Field(description="agent_recommended or client_requested")
    client_feedback: str = Field(default="", description="Any feedback client gave about this property")


class PropertyViewLogger(BaseTool):
    name: str = "property_view_logger"
    description: str = (
        "Logs that a client was shown a specific property. "
        "Agent recommended means you recommend some property and client requested mean client has specifically requested that property"
        "Call this every time you present a property to a client. "
        "This prevents showing the same property twice and tracks viewing history."
    )
    args_schema: Type[BaseModel] = PropertyViewLoggerInput

    async def _arun(
        self,
        phone_number: str,
        property_id: str,
        source: str,
        client_feedback: str = ""
    ) -> str:
        try:
            async with get_async_session() as session:
                view = ClientPropertyViews(
                    client_phone=phone_number,
                    property_id=property_id,
                    viewed_at=datetime.utcnow(),
                    client_feedback=client_feedback
                )
                session.add(view)
                await session.commit()
                return f"Property view logged for client {phone_number}."

        except Exception as e:
            return f"Error logging property view: {str(e)}"

    def _run(self, **kwargs) -> str:
        raise NotImplementedError("Async only.")