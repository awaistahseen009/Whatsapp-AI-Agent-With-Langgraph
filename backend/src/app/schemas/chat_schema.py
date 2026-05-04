from pydantic import BaseModel, Field


class ChatSendRequest(BaseModel):
    client_phone: str = Field(description="The client phone number (thread_id)")
    message: str = Field(description="The text message to send to the agent")


class ChatSendResponse(BaseModel):
    client_phone: str
    user_message: str
    agent_reply: str
    response_type: str
    onboarding_complete: bool
    escalated: bool
    message_count: int
