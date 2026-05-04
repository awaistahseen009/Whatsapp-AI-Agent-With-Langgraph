from sqlmodel import SQLModel, Field, Column, Relationship
import sqlalchemy.dialects.postgresql as pg
from sqlalchemy import text, Enum as SAEnum
from enum import Enum
from datetime import datetime, timedelta
import uuid
from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from src.app.models.security_question import SecurityQuestion


class UserRole(str, Enum):
    OWNER = "owner"
    AGENT = "agent"


class User(SQLModel, table=True):
    __tablename__ = "user"

    id: uuid.UUID = Field(sa_column=Column(
        pg.UUID,
        primary_key=True,
        nullable=False,
        default=uuid.uuid4
    ))
    name: str
    email: str
    role: UserRole = Field(
        sa_column=Column(
            SAEnum(UserRole, name="userrole", values_callable=lambda e: [m.value for m in e]),
            nullable=False,
            server_default="agent"
        )
    )
    password_hash: str = Field(exclude=True)
    created_at: datetime = Field(sa_column=Column(
        pg.TIMESTAMP,
        nullable=False,
        default=datetime.now
    ))
    updated_at: datetime = Field(
        sa_column=Column(
            pg.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=text("now()"),
            onupdate=text("now()")
        )
    )

    security_questions: List["SecurityQuestion"] = Relationship(back_populates="user")
