from sqlmodel import SQLModel, Field, Column, ForeignKey
import sqlalchemy.dialects.postgresql as pg
from enum import Enum
from sqlalchemy import Enum as SAEnum

from datetime import datetime
from typing import Optional

class ClientDocType(str, Enum):
    SALE_DEED = "sale_deed"
    NOC = "noc"
    BANK_STATEMENT = "bank_statement"
    CNIC = "cnic"
    FLOOR_PLAN = "floor_plan"
    BROCHURE = "brochure"
    OTHER = "other"

class StorageStatus(str, Enum):
    INJECTED = "injected"
    CHUNKED = "chunked"

class ClientDocument(SQLModel, table=True):
    __tablename__ = "client_documents"

    doc_id: str = Field(sa_column=Column(pg.VARCHAR, primary_key=True))
    client_phone: str = Field(sa_column=Column(pg.VARCHAR, ForeignKey("client.phone_num"), nullable=False))
    filename: str = Field(sa_column=Column(pg.VARCHAR, nullable=False))
    doc_type: ClientDocType = Field(sa_column=Column(SAEnum(ClientDocType, name= "clientdoctype"), nullable=False))
    page_count: int = Field(sa_column=Column(pg.INTEGER))
    token_count: int = Field(sa_column=Column(pg.INTEGER))
    
    storage_status: StorageStatus = Field(sa_column=Column(SAEnum(StorageStatus, name = "storagestatus")))
    
    created_at: datetime = Field(sa_column=Column(pg.TIMESTAMP, default=datetime.now))
    expires_at: Optional[datetime] = Field(sa_column=Column(pg.TIMESTAMP, nullable=True))
    chunks_cleared: bool = Field(default=False)