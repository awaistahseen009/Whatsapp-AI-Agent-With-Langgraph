from sqlmodel import SQLModel, Field, Column, ForeignKey
import sqlalchemy.dialects.postgresql as pg
from datetime import datetime
import uuid
from typing import Optional

class Transcript(SQLModel, table=True):
    __tablename__ = "transcripts"

    transcript_id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(pg.UUID(as_uuid=True), primary_key=True)
    )
    session_id: uuid.UUID = Field(
        sa_column=Column(pg.UUID(as_uuid=True), ForeignKey("conversation_sessions.session_id"), nullable=False)
    )
    client_phone: str = Field(sa_column=Column(pg.VARCHAR, ForeignKey("client.phone_num"), nullable=False))
    message_content: str = Field(sa_column=Column(pg.TEXT, nullable=False))
    message_type: str = Field(sa_column=Column(pg.VARCHAR, nullable=False))  # 'user', 'assistant', 'system'
    timestamp: datetime = Field(sa_column=Column(pg.TIMESTAMP(timezone=True), default=datetime.now))
    tokens_used: Optional[int] = Field(sa_column=Column(pg.INTEGER, nullable=True))
    processing_time_ms: Optional[int] = Field(sa_column=Column(pg.INTEGER, nullable=True))
    created_at: datetime = Field(
        sa_column=Column(pg.TIMESTAMP(timezone=True), nullable=False, default=datetime.now)
    )
