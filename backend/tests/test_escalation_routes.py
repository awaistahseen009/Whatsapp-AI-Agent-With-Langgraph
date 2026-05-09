import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_get_escalations_empty(async_client: AsyncClient):
    response = await async_client.get("/api/escalations/")
    assert response.status_code == 200
    assert response.json() == []

@pytest.mark.asyncio
async def test_resolve_escalation_not_found(async_client: AsyncClient):
    response = await async_client.put("/api/escalations/00000000-0000-0000-0000-000000000000/resolve/", json={
        "status": "resolved",
        "resolution_notes": "test"
    })
    assert response.status_code == 404
