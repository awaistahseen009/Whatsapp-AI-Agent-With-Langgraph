from sqlmodel import SQLModel, Field, Column
import sqlalchemy.dialects.postgresql as pg
from enum import Enum
from sqlalchemy import Enum as SAEnum
from datetime import datetime , timedelta
from sqlmodel import Relationship
from typing import List, TYPE_CHECKING

import uuid

if TYPE_CHECKING:
    from src.app.models.client_property_views import ClientPropertyViews

class ClientStatus(str, Enum):
    NEW = "new"
    SERIOUS = "serious"
    CONVERTED = "converted"
    LOST = "lost"

class ClientIntent(str , Enum):
    BUY = "buy"
    INVEST = "invest"
    RENT = "rent"

class Client(SQLModel, table = True):
    __tablename__ = "client"

    phone_num:str = Field(sa_column=Column(
        pg.VARCHAR, 
        primary_key=True , 
        nullable = False
    ))
    name:str
    email:str = Field(
        sa_column=Column(
            pg.VARCHAR, 
            nullable = True
        )
    )
    city:str
    timezone:str
    status: ClientStatus = Field(
        sa_column=Column(
            SAEnum(ClientStatus, name="clientstatus"), 
            nullable = False, 
            default = ClientStatus.NEW
        )
    )
    intent: ClientIntent = Field(sa_column=Column(
        SAEnum(ClientIntent, name = "clientintent"), 
        nullable = True ,
    ))
    budget_min: int = Field(sa_column=Column(pg.BIGINT, nullable=True))
    budget_max: int = Field(sa_column=Column(pg.BIGINT, nullable=True))

    preferred_locations: List[str] = Field(sa_column=Column(pg.ARRAY(pg.VARCHAR)))
    property_type_pref: List[str] = Field(sa_column=Column(pg.ARRAY(pg.VARCHAR)))

    loan_preapproved: bool = Field(default=False)
    onboarding_complete: bool = Field(default=False)
    created_at:datetime = Field(
        sa_column=Column(
            pg.TIMESTAMP, 
            nullable = False , 
            default = datetime.now()
        )
    )
    last_active_at:datetime = Field(
        sa_column=Column(
            pg.TIMESTAMP, 
            nullable = False , 
            default = datetime.now()
        )
    )
    views: List["ClientPropertyViews"] = Relationship(back_populates="client")

