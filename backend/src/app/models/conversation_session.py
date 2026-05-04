from sqlmodel import SQLModel, Field, Column, ForeignKey
import sqlalchemy.dialects.postgresql as pg
from sqlalchemy import Enum as SAEnum

from datetime import datetime
import uuid
from typing import Optional

class ConversationSession(SQLModel, table=True):
    __tablename__ = "conversation_sessions"

    session_id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(pg.UUID(as_uuid=True), primary_key=True)
    )
    client_phone: str = Field(sa_column=Column(pg.VARCHAR, ForeignKey("client.phone_num")))
    started_at: datetime = Field(sa_column=Column(pg.TIMESTAMP, default=datetime.now))
    ended_at: Optional[datetime] = Field(sa_column=Column(pg.TIMESTAMP, nullable=True))
    message_count: int = Field(default=0)
    tools_called: dict = Field(default={}, sa_column=Column(pg.JSONB))
    properties_shown: int = Field(default=0)
    meeting_scheduled: bool = Field(default=False)
    escalated: bool = Field(default=False)
    summarization_triggered: bool = Field(default=False)
    total_tokens_in: int = Field(default=0)
    total_tokens_out: int = Field(default=0)
    total_latency_ms: int = Field(default=0)