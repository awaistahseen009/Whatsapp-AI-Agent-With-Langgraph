from sqlmodel import SQLModel, Field, Column
import sqlalchemy.dialects.postgresql as pg
from sqlalchemy import text
from enum import Enum
from datetime import datetime
from typing import List, Optional, Dict
import uuid
from sqlmodel import Relationship
from sqlalchemy import Enum as SAEnum
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.app.models.client_property_views import ClientPropertyViews

class PropertyType(str, Enum):
    APARTMENT = "apartment"
    HOUSE = "house"
    PLOT = "plot"
    VILLA = "villa"
    COMMERCIAL = "commercial"

class ListingType(str, Enum):
    SALE = "sale"
    RENT = "rent"


class Property(SQLModel, table=True):
    __tablename__ = "property"

    property_id: uuid.UUID = Field(        
        sa_column=Column(
            pg.UUID(as_uuid=True), primary_key=True, nullable=False,
                         default = uuid.uuid4)
    )
    title: str = Field(sa_column=Column(pg.VARCHAR, nullable=False))
    description: str = Field(sa_column=Column(pg.TEXT, nullable=True))
    
    property_type: PropertyType = Field(
        sa_column=Column(SAEnum(PropertyType,name = "propertytype"), nullable=False)
    )
    listing_type: ListingType = Field(
        sa_column=Column(SAEnum(ListingType, name = "listingtype"), nullable=False)
    )

    location_area: str = Field(sa_column=Column(pg.VARCHAR)) 
    location_city: str = Field(sa_column=Column(pg.VARCHAR))
    address: str = Field(sa_column=Column(pg.TEXT))

    price: int = Field(sa_column=Column(pg.BIGINT, nullable=False))
    price_negotiable: bool = Field(default=True)

    bedrooms: Optional[int] = Field(default=None)
    bathrooms: Optional[int] = Field(default=None)
    size_sqft: int = Field(sa_column=Column(pg.INTEGER))
    floor_number: Optional[int] = Field(default=None)
    total_floors: Optional[int] = Field(default=None)

    features: Dict = Field(default={}, sa_column=Column(pg.JSONB))

    images: List[str] = Field(default=[], sa_column=Column(pg.ARRAY(pg.VARCHAR)))

    available: bool = Field(default=True)
    developer_name: Optional[str] = Field(default=None)
    
    created_at: datetime = Field(
        sa_column=Column(
            pg.TIMESTAMP(timezone=True), 
            nullable=False, 
            server_default=text("now()")
        )
    )
    updated_at: datetime = Field(
        sa_column=Column(
            pg.TIMESTAMP(timezone=True), 
            nullable=False, 
            server_default=text("now()"),
            onupdate=text("now()")
        )
    )
    views: List["ClientPropertyViews"] = Relationship(back_populates="property")