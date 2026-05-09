import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_get_meetings_empty(async_client: AsyncClient):
    response = await async_client.get("/api/meetings/")
    assert response.status_code == 200
    assert response.json() == []

@pytest.mark.asyncio
async def test_get_meeting_not_found(async_client: AsyncClient):
    response = await async_client.get("/api/meetings/00000000-0000-0000-0000-000000000000/")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_get_meeting_details_not_found(async_client: AsyncClient):
    response = await async_client.get("/api/meetings/00000000-0000-0000-0000-000000000000/details/")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_update_meeting_not_found(async_client: AsyncClient):
    response = await async_client.put("/api/meetings/00000000-0000-0000-0000-000000000000/", json={
        "status": "confirmed"
    })
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_delete_meeting_not_found(async_client: AsyncClient):
    response = await async_client.delete("/api/meetings/00000000-0000-0000-0000-000000000000/")
    assert response.status_code == 404
