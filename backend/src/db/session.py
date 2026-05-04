from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import AsyncGenerator
from contextlib import asynccontextmanager

from sqlmodel import SQLModel
from config import Config


async_engine = create_async_engine(
    url = Config.DATABASE_URL,
    echo = Config.SQL_ECHO
)

@asynccontextmanager
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async_session = async_sessionmaker(
        bind=async_engine,
        expire_on_commit=False,
        class_=AsyncSession
    )
    async with async_session() as session:
        yield session

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency generator for FastAPI."""
    async with get_async_session() as session:
        yield session
