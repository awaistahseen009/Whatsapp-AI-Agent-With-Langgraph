from sqlmodel import SQLModel, Field, Column, Relationship
import sqlalchemy.dialects.postgresql as pg
from sqlalchemy import ForeignKey
from datetime import datetime
import uuid
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.app.models.user import User


class SecurityQuestion(SQLModel, table=True):
    __tablename__ = "security_questions"

    question_id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(pg.UUID(as_uuid=True), primary_key=True, nullable=False)
    )
    user_id: uuid.UUID = Field(
        sa_column=Column(pg.UUID(as_uuid=True), ForeignKey("user.id"), nullable=False)
    )
    question: str = Field(sa_column=Column(pg.TEXT, nullable=False))
    answer_hash: str = Field(sa_column=Column(pg.TEXT, nullable=False))
    created_at: datetime = Field(
        sa_column=Column(pg.TIMESTAMP(timezone=True), nullable=False, default=datetime.now)
    )

    user: "User" = Relationship(back_populates="security_questions")
