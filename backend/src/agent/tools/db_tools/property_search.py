from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type, Optional
from sqlmodel import select
from sqlalchemy import and_
from src.db.session import get_async_session
from src.app.models.property import Property, PropertyType, ListingType


class PropertySearchInput(BaseModel):
    listing_type: Optional[str] = Field(default=None, description="sale or rent")
    property_type: Optional[str] = Field(default=None, description="apartment, house, plot, villa, commercial")
    location_city: Optional[str] = Field(default=None, description="City to search in")
    location_area: Optional[str] = Field(default=None, description="Specific area or neighborhood")
    min_price: Optional[int] = Field(
        default=None,
        description="Minimum price filter (use for 'at least', 'starting from', 'between X and Y')"
    )
    max_price: Optional[int] = Field(
        default=None,
        description="Maximum price filter (use for 'at most', 'under', 'up to', 'between X and Y', 'around X' → set ±20%)"
    )
    min_bedrooms: Optional[int] = Field(
        default=None,
        description="Minimum number of bedrooms (use for 'at least N bedrooms'). Use this instead of exact match."
    )
    max_bedrooms: Optional[int] = Field(
        default=None,
        description="Maximum number of bedrooms (use for 'at most N bedrooms', or set equal to min_bedrooms for exact match)"
    )
    min_bathrooms: Optional[int] = Field(
        default=None,
        description="Minimum number of bathrooms"
    )
    min_sqft: Optional[int] = Field(
        default=None,
        description="Minimum square footage"
    )
    available_only: bool = Field(default=True, description="Only return available properties")
    limit: int = Field(default=5, description="Max number of results to return (increase to 10 if client wants more options)")


class PropertySearchTool(BaseTool):
    name: str = "property_search"
    description: str = (
        "Search live property listings from the database. "
        "Call this when client gives specific criteria — location, type, price range, bedrooms. "
        "Results reflect real-time availability. Always use this rather than guessing from memory. "
        "PRICE TIPS: "
        "'around 200k' → min_price=160000, max_price=240000 (±20%). "
        "'under 300k' → max_price=300000. "
        "'between 100k and 200k' → min_price=100000, max_price=200000. "
        "BEDROOMS: 'at least 3 bedrooms' → min_bedrooms=3. '2 bedrooms' → min_bedrooms=2, max_bedrooms=2."
    )
    args_schema: Type[BaseModel] = PropertySearchInput

    async def _arun(
        self,
        listing_type: Optional[str] = None,
        property_type: Optional[str] = None,
        location_city: Optional[str] = None,
        location_area: Optional[str] = None,
        min_price: Optional[int] = None,
        max_price: Optional[int] = None,
        min_bedrooms: Optional[int] = None,
        max_bedrooms: Optional[int] = None,
        min_bathrooms: Optional[int] = None,
        min_sqft: Optional[int] = None,
        available_only: bool = True,
        limit: int = 5
    ) -> str:
        try:
            async with get_async_session() as session:
                filters = []

                if available_only:
                    filters.append(Property.available == True)
                if listing_type:
                    filters.append(Property.listing_type == ListingType(listing_type))
                if property_type:
                    filters.append(Property.property_type == PropertyType(property_type))
                if location_city:
                    filters.append(Property.location_city.ilike(f"%{location_city}%"))
                if location_area:
                    filters.append(Property.location_area.ilike(f"%{location_area}%"))
                if min_price is not None:
                    filters.append(Property.price >= min_price)
                if max_price is not None:
                    filters.append(Property.price <= max_price)
                if min_bedrooms is not None:
                    filters.append(Property.bedrooms >= min_bedrooms)
                if max_bedrooms is not None:
                    filters.append(Property.bedrooms <= max_bedrooms)
                if min_bathrooms is not None:
                    filters.append(Property.bathrooms >= min_bathrooms)
                if min_sqft is not None:
                    filters.append(Property.size_sqft >= min_sqft)

                query = select(Property).where(and_(*filters)).limit(limit)
                result = await session.execute(query)
                properties = result.scalars().all()

                if not properties:
                    # ── Fallback: broaden price range by 30% ──────────────
                    if min_price is not None or max_price is not None:
                        relaxed_filters = [f for f in filters]
                        # Remove old price filters and widen
                        relaxed_filters = []
                        if available_only:
                            relaxed_filters.append(Property.available == True)
                        if listing_type:
                            relaxed_filters.append(Property.listing_type == ListingType(listing_type))
                        if property_type:
                            relaxed_filters.append(Property.property_type == PropertyType(property_type))
                        if location_city:
                            relaxed_filters.append(Property.location_city.ilike(f"%{location_city}%"))
                        if min_price is not None:
                            relaxed_filters.append(Property.price >= int(min_price * 0.7))
                        if max_price is not None:
                            relaxed_filters.append(Property.price <= int(max_price * 1.3))
                        if min_bedrooms is not None:
                            relaxed_filters.append(Property.bedrooms >= min_bedrooms)

                        query2 = select(Property).where(and_(*relaxed_filters)).limit(limit)
                        result2 = await session.execute(query2)
                        properties = result2.scalars().all()

                        if properties:
                            output = (
                                f"No exact matches found. Here are {len(properties)} "
                                f"nearby option(s) with a wider price range:\n\n"
                            )
                            return output + self._format_results(properties)

                    return "No properties found matching the given criteria."

                output = f"Found {len(properties)} propert{'y' if len(properties) == 1 else 'ies'}:\n\n"
                return output + self._format_results(properties)

        except Exception as e:
            return f"Error searching properties: {str(e)}"

    @staticmethod
    def _format_results(properties) -> str:
        output = ""
        for p in properties:
            features_str = ""
            if p.features and isinstance(p.features, dict):
                feat_list = p.features.get("list", [])
                if feat_list:
                    features_str = f"Features: {', '.join(feat_list[:5])}\n"
            output += (
                f"ID: {p.property_id}\n"
                f"Title: {p.title}\n"
                f"Type: {p.property_type.value} — {p.listing_type.value}\n"
                f"Location: {p.location_area}, {p.location_city}\n"
                f"Price: ${p.price:,}{'(negotiable)' if p.price_negotiable else ''}\n"
                f"Bedrooms: {p.bedrooms or 'N/A'} | Bathrooms: {p.bathrooms or 'N/A'}\n"
                f"Size: {p.size_sqft:,} sqft\n"
                f"{features_str}"
                f"Developer: {p.developer_name or 'N/A'}\n"
                f"Description: {p.description or 'N/A'}\n"
                f"{'─' * 40}\n"
            )
        return output

    def _run(self, **kwargs) -> str:
        raise NotImplementedError("Async only.")