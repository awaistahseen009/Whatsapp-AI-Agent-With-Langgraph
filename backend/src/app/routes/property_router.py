from fastapi import APIRouter, Depends, status, Query
from sqlmodel.ext.asyncio.session import AsyncSession
from src.db.session import get_db_session as get_session
from src.app.schemas.property_schema import PropertyCreateSchema, PropertyUpdateSchema
from src.app.services.property_service import PropertyService
from src.app.dependencies.bearer import AccessTokenBearer, RoleChecker
from fastapi.exceptions import HTTPException
from typing import Optional

service = PropertyService()
property_router = APIRouter()


@property_router.get("/")
async def list_properties(
    city: Optional[str] = None,
    property_type: Optional[str] = None,
    listing_type: Optional[str] = None,
    min_price: Optional[int] = None,
    max_price: Optional[int] = None,
    bedrooms: Optional[int] = None,
    available_only: bool = True,
    offset: int = 0,
    limit: int = 20,
    token_data: dict = Depends(AccessTokenBearer()),
    session: AsyncSession = Depends(get_session),
):
    props = await service.list_properties(
        session, city, property_type, listing_type,
        min_price, max_price, bedrooms, available_only, offset, limit
    )
    return [p.model_dump() for p in props]


@property_router.get("/{property_id}")
async def get_property(
    property_id: str,
    token_data: dict = Depends(AccessTokenBearer()),
    session: AsyncSession = Depends(get_session),
):
    prop = await service.get_property(property_id, session)
    if not prop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
    return prop.model_dump()


@property_router.post("/", status_code=status.HTTP_201_CREATED)
async def create_property(
    data: PropertyCreateSchema,
    token_data: dict = Depends(RoleChecker(["owner"])),
    session: AsyncSession = Depends(get_session),
):
    prop = await service.create_property(data, session)
    return prop.model_dump()


@property_router.put("/{property_id}")
async def update_property(
    property_id: str,
    data: PropertyUpdateSchema,
    token_data: dict = Depends(RoleChecker(["owner"])),
    session: AsyncSession = Depends(get_session),
):
    prop = await service.update_property(property_id, data, session)
    if not prop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
    return prop.model_dump()


@property_router.delete("/{property_id}")
async def delete_property(
    property_id: str,
    token_data: dict = Depends(RoleChecker(["owner"])),
    session: AsyncSession = Depends(get_session),
):
    deleted = await service.delete_property(property_id, session)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
    return {"message": "Property deleted successfully"}
