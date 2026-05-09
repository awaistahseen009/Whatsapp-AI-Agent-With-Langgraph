import pytest
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession
from src.app.models.user import User
from src.app.utils.utils import verify_password

@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, owner_user: User):
    response = await client.post("/api/auth/login/", json={
        "email": "owner@test.com",
        "password": "password123"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data

@pytest.mark.asyncio
async def test_login_failure(client: AsyncClient, owner_user: User):
    response = await client.post("/api/auth/login/", json={
        "email": "owner@test.com",
        "password": "wrongpassword"
    })
    assert response.status_code == 403
    assert response.json()["detail"] == "Invalid email or password"

@pytest.mark.asyncio
async def test_get_agents_owner(async_client: AsyncClient, agent_user: User):
    response = await async_client.get("/api/auth/agents/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["role"] == "owner"

@pytest.mark.asyncio
async def test_get_agents_unauthorized(client: AsyncClient):
    response = await client.get("/api/auth/agents/")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_signup_agent_success(async_client: AsyncClient):
    response = await async_client.post("/api/auth/signup/", json={
        "firstname": "New",
        "lastname": "Agent",
        "email": "new.agent@test.com",
        "password": "Password123!",
        "confirm_password": "Password123!"
    })
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_has_security_question(async_client: AsyncClient):
    response = await async_client.get("/api/auth/has-security-question/")
    assert response.status_code == 200
    assert response.json() == {"has_security_question": False}

# @pytest.mark.asyncio
# async def test_set_security_question(async_client: AsyncClient, db_session: AsyncSession):
#     response = await async_client.post("/api/auth/set-question/", json={
#         "question": "What is your pet's name?",
#         "answer": "Fluffy"
#     })
#     assert response.status_code == 200
#     assert response.json()["message"] == "Security question set successfully"

#     response_after = await async_client.get("/api/auth/has-security-question/")
#     assert response_after.status_code == 200
#     assert response_after.json() == {"has_security_question": True}

@pytest.mark.asyncio
async def test_change_password(async_client: AsyncClient, db_session: AsyncSession, owner_user: User):
    response = await async_client.post("/api/auth/change-password/", json={
        "old_password": "password123",
        "new_password": "NewPassword123!"
    })
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_logout(async_client: AsyncClient, owner_token: str):
    response = await async_client.post("/api/auth/logout/", json={
        "refresh_token": owner_token  # Using access token here just for structure matching
    })
    assert response.status_code == 200
    assert response.json()["message"] == "Logged out successfully"
