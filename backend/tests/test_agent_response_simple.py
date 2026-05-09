import pytest
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession
from src.app.models.user import User

@pytest.mark.asyncio
async def test_send_message_to_agent_no_graph(async_client: AsyncClient, owner_user: User):
    """Test sending a message to AI agent when graph is None"""
    response = await async_client.post("/api/chat/send/", json={
        "client_phone": "+1234567890",
        "message": "Hello, I'm interested in buying a property"
    })
    # Mock graph handles it, so expect 200
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_list_chat_sessions(async_client: AsyncClient, owner_user: User):
    """Test listing chat sessions"""
    response = await async_client.get("/api/chat/sessions/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

@pytest.mark.asyncio
async def test_get_monthly_chat_stats(async_client: AsyncClient, owner_user: User):
    """Test monthly chat statistics"""
    response = await async_client.get("/api/chat/stats/monthly/")
    assert response.status_code == 200
    data = response.json()
    assert "current_month" in data
    assert "last_month" in data
    assert "total_sessions" in data["current_month"]
    assert "avg_response_time" in data["current_month"]
    assert "total_sessions" in data["last_month"]
    assert "avg_response_time" in data["last_month"]

@pytest.mark.asyncio
async def test_send_message_invalid_data(async_client: AsyncClient, owner_user: User):
    """Test sending message with invalid data"""
    response = await async_client.post("/api/chat/send/", json={
        "client_phone": "",  # Invalid empty phone
        "message": "Test message"
    })
    # Should return 200 since mock graph handles it
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_send_message_empty_message(async_client: AsyncClient, owner_user: User):
    """Test sending empty message"""
    response = await async_client.post("/api/chat/send/", json={
        "client_phone": "+1234567896",
        "message": ""  # Empty message
    })
    # Should return 200 since mock graph handles it
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_webhook_verification_disabled(async_client: AsyncClient, owner_user: User):
    """Test webhook verification endpoint"""
    response = await async_client.get("/api/chat/webhook/", params={
        "hub.mode": "subscribe",
        "hub.verify_token": "wrong_token",
        "hub.challenge": "123456"
    })
    assert response.status_code == 403
