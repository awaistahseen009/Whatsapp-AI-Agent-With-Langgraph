import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_get_logs_tokens_owner(async_client: AsyncClient):
    response = await async_client.get("/api/logs/tokens/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_get_logs_tokens_agent(agent_client: AsyncClient):
    response = await agent_client.get("/api/logs/tokens/")
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_get_logs_tools_owner(async_client: AsyncClient):
    response = await async_client.get("/api/logs/tools/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_get_logs_tools_agent(agent_client: AsyncClient):
    response = await agent_client.get("/api/logs/tools/")
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_get_logs_errors_owner(async_client: AsyncClient):
    response = await async_client.get("/api/logs/errors/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_get_logs_errors_agent(agent_client: AsyncClient):
    response = await agent_client.get("/api/logs/errors/")
    assert response.status_code == 403
