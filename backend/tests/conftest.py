import pytest
import pytest_asyncio
import asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import sessionmaker

from src.app.main import app
from src.db.session import get_db_session
from src.app.models.user import User, UserRole
from src.app.utils.utils import create_access_token, generate_hash_password
from src.db.redis import token_blacklist_client
from config import Config

from sqlalchemy.pool import NullPool

# Override Redis configuration for tests
Config.REDIS_HOST = "localhost"
Config.REDIS_PORT = "6379"

# Mock Redis client for tests to avoid connection issues
class MockRedisClient:
    def __init__(self):
        self.data = {}
    
    async def get(self, key):
        return self.data.get(key)
    
    async def set(self, name, value, ex=None, nx=False):
        if nx and name in self.data:
            return None
        self.data[name] = value
        return True
    
    async def delete(self, *keys):
        for key in keys:
            self.data.pop(key, None)
        return len(keys)

# Create mock Redis client
test_redis_client = MockRedisClient()

# Patch the Redis module to use mock client
import src.db.redis
src.db.redis.token_blacklist_client = test_redis_client

# Use DATABASE_URL from environment (via Config)
TEST_DATABASE_URL = Config.DATABASE_URL

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    poolclass=NullPool
)

TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=test_engine, class_=AsyncSession
)

async def override_get_db_session():
    async with TestingSessionLocal() as session:
        yield session

# Override the DB dependency
app.dependency_overrides[get_db_session] = override_get_db_session

# Set up mock graph for tests
from unittest.mock import AsyncMock

# Create a mock graph that returns realistic responses
mock_graph = AsyncMock()
mock_graph.ainvoke.return_value = {
    "messages": [
        type('MockAIMessage', (), {
            'content': "I'm a test AI response for testing purposes."
        })
    ],
    "response_type": "text",
    "onboarding_complete": True,
    "escalated": False,
    "message_count": 1
}

app.state.graph = mock_graph

# Import Alembic components for migrations
from alembic.config import Config as AlembicConfig
from alembic import command
import os

def run_alembic_migrations():
    """Run Alembic migrations on the test database."""
    # Get backend root directory (parent of tests)
    backend_dir = os.path.join(os.path.dirname(__file__), "..")
    alembic_ini = os.path.join(backend_dir, "alembic.ini")
    
    # Create Alembic config
    alembic_cfg = AlembicConfig(alembic_ini)
    # Set the database URL from Config (sync version for alembic)
    alembic_cfg.set_main_option("sqlalchemy.url", Config.DATABASE_URL.replace("+asyncpg", ""))
    
    # Run migrations
    command.upgrade(alembic_cfg, "head")

@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_db():
    """Run Alembic migrations before all tests."""
    # Run migrations on real database
    await asyncio.to_thread(run_alembic_migrations)
    yield
    # Note: We don't drop tables after tests on real database
    # This allows inspecting the database after test runs

@pytest_asyncio.fixture(scope="function")
async def db_session(setup_db):
    """Returns a test database session."""
    async with TestingSessionLocal() as session:
        yield session

@pytest_asyncio.fixture(scope="function")
async def client():
    """Unauthenticated test client."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as ac:
        yield ac

@pytest_asyncio.fixture(scope="function")
async def owner_user(db_session: AsyncSession):
    """Creates and returns an owner user."""
    user = User(
        name="Test Owner",
        email="owner@test.com",
        password_hash=generate_hash_password("password123"),
        role=UserRole.OWNER,
        firstname="Test",
        lastname="Owner"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest_asyncio.fixture(scope="function")
async def agent_user(db_session: AsyncSession):
    """Creates and returns an agent user."""
    user = User(
        name="Test Agent",
        email="agent@test.com",
        password_hash=generate_hash_password("password123"),
        role=UserRole.AGENT,
        firstname="Test",
        lastname="Agent"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest_asyncio.fixture(scope="function")
async def owner_token(owner_user: User):
    """Returns a valid access token for an owner."""
    user_data = {
        "user_id": str(owner_user.id),
        "email": owner_user.email,
        "name": owner_user.name,
        "role": owner_user.role.value
    }
    return create_access_token(user_data)

@pytest_asyncio.fixture(scope="function")
async def agent_token(agent_user: User):
    """Returns a valid access token for an agent."""
    user_data = {
        "user_id": str(agent_user.id),
        "email": agent_user.email,
        "name": agent_user.name,
        "role": agent_user.role.value
    }
    return create_access_token(user_data)

@pytest_asyncio.fixture(scope="function")
async def async_client(owner_token):
    """Authenticated test client (Owner)."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
        headers={"Authorization": f"Bearer {owner_token}"}
    ) as ac:
        yield ac

@pytest_asyncio.fixture(scope="function")
async def agent_client(agent_token):
    """Authenticated test client (Agent)."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
        headers={"Authorization": f"Bearer {agent_token}"}
    ) as ac:
        yield ac
