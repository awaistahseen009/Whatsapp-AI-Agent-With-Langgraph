import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_get_clients_empty(async_client: AsyncClient):
    response = await async_client.get("/api/clients/")
    assert response.status_code == 200
    assert response.json() == []

@pytest.mark.asyncio
async def test_get_client_monthly_stats(async_client: AsyncClient):
    response = await async_client.get("/api/clients/stats/monthly/")
    assert response.status_code == 200
    data = response.json()
    assert "labels" in data
    assert "data" in data
