from sqlmodel import SQLModel, Field, Column
import sqlalchemy.dialects.postgresql as pg
from enum import Enum
from sqlalchemy import Enum as SAEnum

from datetime import datetime

class CompanyDocType(str, Enum):
    PROPERTY_LISTING = "property_listing"
    AREA_GUIDE = "area_guide"
    POLICY = "policy"
    FAQ = "faq"
    DEVELOPER_PROFILE = "developer_profile"
    LEGAL = "legal"

class CompanyDocument(SQLModel, table=True):
    __tablename__ = "company_documents"

    doc_id: str = Field(sa_column=Column(pg.VARCHAR, primary_key=True))
    filename: str = Field(sa_column=Column(pg.VARCHAR, nullable=False))
    doc_type: CompanyDocType = Field(sa_column=Column(SAEnum(CompanyDocType, name = "companydoctype"), nullable=False))
    chunk_count: int = Field(sa_column=Column(pg.INTEGER, nullable=False))
    token_count: int = Field(sa_column=Column(pg.INTEGER, nullable=False))
    ingested_at: datetime = Field(sa_column=Column(pg.TIMESTAMP, default=datetime.now))
    last_updated_at: datetime = Field(sa_column=Column(pg.TIMESTAMP, default=datetime.now))
    is_active: bool = Field(default=True)