from sqlmodel import SQLModel, Field, Column, ForeignKey
import sqlalchemy.dialects.postgresql as pg
from enum import Enum
from datetime import datetime
import uuid
from sqlalchemy import Enum as SAEnum

from typing import Optional

class RetryStatus(str, Enum):
    PENDING = "pending"
    RETRIED = "retried"
    ABANDONED = "abandoned"

class TokenLog(SQLModel, table=True):
    __tablename__ = "token_logs"
    log_id: uuid.UUID = Field(default_factory=uuid.uuid4, sa_column=Column(pg.UUID(as_uuid=True), primary_key=True))
    client_phone: Optional[str] = Field(sa_column=Column(pg.VARCHAR, nullable=True))
    session_id: uuid.UUID = Field(sa_column=Column(pg.UUID(as_uuid=True), ForeignKey("conversation_sessions.session_id")))
    node_name: str
    model_name: str
    tokens_in: int
    tokens_out: int
    latency_ms: int
    cost_usd: float = Field(sa_column=Column(pg.NUMERIC(10, 6)))
    created_at: datetime = Field(sa_column=Column(pg.TIMESTAMP, default=datetime.now))

class ToolExecutionLog(SQLModel, table=True):
    __tablename__ = "tool_execution_logs"
    log_id: uuid.UUID = Field(default_factory=uuid.uuid4, sa_column=Column(pg.UUID(as_uuid=True), primary_key=True))
    client_phone: Optional[str] = Field(sa_column=Column(pg.VARCHAR, nullable=True))
    session_id: uuid.UUID = Field(sa_column=Column(pg.UUID(as_uuid=True), ForeignKey("conversation_sessions.session_id")))
    tool_name: str
    success: bool
    error_message: Optional[str] = Field(sa_column=Column(pg.TEXT, nullable=True))
    execution_time_ms: int
    created_at: datetime = Field(sa_column=Column(pg.TIMESTAMP, default=datetime.now))

class ErrorLog(SQLModel, table=True):
    __tablename__ = "error_logs"
    error_id: uuid.UUID = Field(default_factory=uuid.uuid4, sa_column=Column(pg.UUID(as_uuid=True), primary_key=True))
    client_phone: Optional[str] = Field(sa_column=Column(pg.VARCHAR, nullable=True))
    thread_id: str
    node_name: str
    incoming_message: str = Field(sa_column=Column(pg.TEXT))
    error_type: str
    error_message: str = Field(sa_column=Column(pg.TEXT))
    traceback: str = Field(sa_column=Column(pg.TEXT))
    retry_count: int = Field(default=0)
    retry_status: RetryStatus = Field(sa_column=Column(SAEnum(RetryStatus, name = "retrystatus"), default=RetryStatus.PENDING))
    created_at: datetime = Field(sa_column=Column(pg.TIMESTAMP, default=datetime.now))