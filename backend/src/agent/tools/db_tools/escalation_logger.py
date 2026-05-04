from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type
from datetime import datetime
from src.db.session import get_async_session
from src.app.models.escalation import Escalation, EscalationStatus


class EscalationLoggerInput(BaseModel):
    client_phone: str = Field(description="Client's WhatsApp phone number")
    reason: str = Field(description="Why escalation was triggered")
    conversation_summary: str = Field(description="Current rolling summary of the conversation")
    last_client_message: str = Field(description="The last message the client sent before escalation")


class EscalationLogger(BaseTool):
    name: str = "escalation_logger"
    description: str = (
        "Logs an escalation to the database and flags the conversation for human review. "
        "Call this when handing off to a human — frustrated client, legal question, "
        "explicit human request, or high-value negotiation moment. "
        "After calling this, inform the client a team member will be with them shortly."
    )
    args_schema: Type[BaseModel] = EscalationLoggerInput

    async def _arun(
        self,
        client_phone: str,
        reason: str,
        conversation_summary: str,
        last_client_message: str
    ) -> str:
        try:
            async with get_async_session() as session:
                escalation = Escalation(
                    client_phone=client_phone,
                    triggered_at=datetime.utcnow(),
                    reason=reason,
                    conversation_summary=conversation_summary,
                    last_client_message=last_client_message,
                    status=EscalationStatus.PENDING
                )
                session.add(escalation)
                await session.commit()
                await session.refresh(escalation)

                return (
                    f"Escalation logged successfully.\n"
                    f"Escalation ID: {escalation.escalation_id}\n"
                    f"Status: {escalation.status.value}\n"
                    f"The conversation is now flagged for human review."
                )

        except Exception as e:
            return f"Error logging escalation: {str(e)}"

    def _run(self, **kwargs) -> str:
        raise NotImplementedError("Async only.")