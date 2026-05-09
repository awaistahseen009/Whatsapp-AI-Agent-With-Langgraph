import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_get_chat_sessions(async_client: AsyncClient):
    response = await async_client.get("/api/chat/sessions/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

# @pytest.mark.asyncio
# async def test_verify_webhook_success(client: AsyncClient):
#     # Tests the Meta webhook verification with hardcoded "my_custom_verify_token"
#     response = await client.get("/api/chat/webhook/", params={
#         "hub.mode": "subscribe",
#         "hub.verify_token": "my_custom_verify_token",
#         "hub.challenge": "123456"
#     })
#     assert response.status_code == 200
#     assert response.text == "123456"

@pytest.mark.asyncio
async def test_verify_webhook_failure(client: AsyncClient):
    response = await client.get("/api/chat/webhook/", params={
        "hub.mode": "subscribe",
        "hub.verify_token": "wrong_token",
        "hub.challenge": "123456"
    })
    assert response.status_code == 403
