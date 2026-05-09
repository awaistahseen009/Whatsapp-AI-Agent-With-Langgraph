import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_get_properties_empty(async_client: AsyncClient):
    response = await async_client.get("/api/properties/")
    assert response.status_code == 200
    assert response.json() == []

@pytest.mark.asyncio
async def test_create_property(async_client: AsyncClient):
    response = await async_client.post("/api/properties/", json={
        "title": "Test Property",
        "description": "A very nice test property",
        "price": 500000.0,
        "location": "Test City",
        "bedrooms": 3,
        "bathrooms": 2.5,
        "property_type": "house"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Property"
    assert "property_id" in data

@pytest.mark.asyncio
async def test_get_property_not_found(async_client: AsyncClient):
    response = await async_client.get("/api/properties/00000000-0000-0000-0000-000000000000/")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_update_property_not_found(async_client: AsyncClient):
    response = await async_client.put("/api/properties/00000000-0000-0000-0000-000000000000/", json={
        "title": "Updated Property"
    })
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_delete_property_not_found(async_client: AsyncClient):
    response = await async_client.delete("/api/properties/00000000-0000-0000-0000-000000000000/")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_property_count(async_client: AsyncClient):
    response = await async_client.get("/api/properties/count/")
    assert response.status_code == 200
    assert "total" in response.json()
