import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import sessionmaker

from src.app.main import app
from src.db.session import get_db_session
from src.app.models.user import User, UserRole
from src.app.utils.utils import create_access_token, generate_hash_password

from sqlalchemy.pool import NullPool

# Use proper asyncpg URL for the local postgres container
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:test@localhost:5432/postgres"

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

# Skip the complex Langgraph state setup during normal test runs
from contextlib import asynccontextmanager
@asynccontextmanager
async def test_lifespan(app_instance):
    app_instance.state.graph = None
    yield

app.router.lifespan_context = test_lifespan

@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_db():
    """Create all tables before each test and drop them after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)

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
