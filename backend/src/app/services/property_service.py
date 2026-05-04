from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from src.app.models.property import Property, PropertyType, ListingType
from src.app.schemas.property_schema import PropertyCreateSchema, PropertyUpdateSchema
from typing import Optional
import uuid


class PropertyService:
    async def list_properties(
        self,
        session: AsyncSession,
        city: Optional[str] = None,
        property_type: Optional[str] = None,
        listing_type: Optional[str] = None,
        min_price: Optional[int] = None,
        max_price: Optional[int] = None,
        bedrooms: Optional[int] = None,
        available_only: bool = True,
        offset: int = 0,
        limit: int = 20,
    ):
        statement = select(Property)
        if available_only:
            statement = statement.where(Property.available == True)
        if city:
            statement = statement.where(Property.location_city.ilike(f"%{city}%"))
        if property_type:
            statement = statement.where(Property.property_type == property_type)
        if listing_type:
            statement = statement.where(Property.listing_type == listing_type)
        if min_price is not None:
            statement = statement.where(Property.price >= min_price)
        if max_price is not None:
            statement = statement.where(Property.price <= max_price)
        if bedrooms is not None:
            statement = statement.where(Property.bedrooms >= bedrooms)
        statement = statement.offset(offset).limit(limit)
        result = await session.exec(statement)
        return result.all()

    async def get_property(self, property_id: str, session: AsyncSession):
        statement = select(Property).where(Property.property_id == property_id)
        result = await session.exec(statement)
        return result.first()

    async def create_property(self, data: PropertyCreateSchema, session: AsyncSession):
        prop = Property(**data.model_dump())
        session.add(prop)
        await session.commit()
        await session.refresh(prop)
        return prop

    async def update_property(self, property_id: str, data: PropertyUpdateSchema, session: AsyncSession):
        prop = await self.get_property(property_id, session)
        if not prop:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(prop, key, value)
        session.add(prop)
        await session.commit()
        await session.refresh(prop)
        return prop

    async def delete_property(self, property_id: str, session: AsyncSession):
        prop = await self.get_property(property_id, session)
        if not prop:
            return False
        await session.delete(prop)
        await session.commit()
        return True
