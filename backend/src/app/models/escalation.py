from sqlmodel import SQLModel, Field, Column, ForeignKey
import sqlalchemy.dialects.postgresql as pg
from enum import Enum
from sqlalchemy import Enum as SAEnum

from datetime import datetime
import uuid
from typing import Optional

class EscalationStatus(str, Enum):
    PENDING = "pending"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"

class Escalation(SQLModel, table=True):
    __tablename__ = "escalations"

    escalation_id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(pg.UUID(as_uuid=True), primary_key=True, nullable=False)
    )
    client_phone: str = Field(sa_column=Column(pg.VARCHAR, ForeignKey("client.phone_num"), nullable=False))
    triggered_at: datetime = Field(
        sa_column=Column(pg.TIMESTAMP(timezone=True), nullable=False, default=datetime.now)
    )
    reason: str = Field(sa_column=Column(pg.TEXT, nullable=False))
    conversation_summary: str = Field(sa_column=Column(pg.TEXT, nullable=False))
    last_client_message: str = Field(sa_column=Column(pg.TEXT, nullable=False))
    
    status: EscalationStatus = Field(
        sa_column=Column(SAEnum(EscalationStatus, name = "escalationstatus"), nullable=False, default=EscalationStatus.PENDING)
    )
    resolved_at: Optional[datetime] = Field(sa_column=Column(pg.TIMESTAMP(timezone=True), nullable=True))
    resolution_notes: Optional[str] = Field(sa_column=Column(pg.TEXT, nullable=True))