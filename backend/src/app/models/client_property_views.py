from sqlmodel import SQLModel, Field, Column, Relationship
import sqlalchemy.dialects.postgresql as pg
from enum import Enum
from datetime import datetime , timedelta
from typing import List,TYPE_CHECKING
import uuid
if TYPE_CHECKING:
    from models.client import Client
    from models.property import Property

class ClientPropertyViews(SQLModel, table = True):
    __tablename__ = "client_property_views"

    view_id:uuid.UUID = Field(
        sa_column=Column(
            pg.UUID, 
            nullable=False , 
            primary_key=True,
            default = uuid.uuid4
        )
    )

    client_phone:str = Field(foreign_key="client.phone_num")
    property_id:uuid.UUID = Field(foreign_key="property.property_id")
    viewed_at:datetime = Field(
        sa_column=Column(
            pg.TIMESTAMP, 
            nullable = False ,
            default = datetime.now()
        )
    )
    client_feedback:str
    client: "Client" = Relationship(back_populates="views")
    property: "Property" = Relationship(back_populates="views")