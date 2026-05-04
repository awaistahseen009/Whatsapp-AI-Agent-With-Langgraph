from pydantic import BaseModel, Field
from typing import Optional, List, Dict


class PropertyCreateSchema(BaseModel):
    title: str = Field(description="Property listing title")
    description: Optional[str] = None
    property_type: str = Field(description="apartment, house, plot, villa, commercial")
    listing_type: str = Field(description="sale or rent")
    location_area: str = Field(description="Area/neighborhood name")
    location_city: str = Field(description="City name")
    address: str = Field(description="Full street address")
    price: int = Field(gt=0, description="Price in USD")
    price_negotiable: bool = True
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    size_sqft: int = Field(gt=0, description="Size in square feet")
    floor_number: Optional[int] = None
    total_floors: Optional[int] = None
    features: Dict = Field(default={})
    images: List[str] = Field(default=[])
    available: bool = True
    developer_name: Optional[str] = None


class PropertyUpdateSchema(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    property_type: Optional[str] = None
    listing_type: Optional[str] = None
    location_area: Optional[str] = None
    location_city: Optional[str] = None
    address: Optional[str] = None
    price: Optional[int] = None
    price_negotiable: Optional[bool] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    size_sqft: Optional[int] = None
    floor_number: Optional[int] = None
    total_floors: Optional[int] = None
    features: Optional[Dict] = None
    images: Optional[List[str]] = None
    available: Optional[bool] = None
    developer_name: Optional[str] = None
