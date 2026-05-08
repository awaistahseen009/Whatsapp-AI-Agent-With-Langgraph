import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context
from config import Config
import sqlmodel
from sqlmodel import SQLModel
from src.app.models.client import *
from src.app.models.client_document import *
from src.app.models.client_property_views import *
from src.app.models.company_document import *
from src.app.models.conversation_session import *
from src.app.models.escalation import *
from src.app.models.logs import *
from src.app.models.meeting import *
from src.app.models.property import *
from src.app.models.user import *
from src.app.models.security_question import *

import alembic_postgresql_enum  # noqa – required for enum handling

# Alembic Config object
config = context.config

# Setup logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Database URL – keep asyncpg but remove any query parameters (?sslmode=...)
raw_url = Config.DATABASE_URL
# Remove everything after '?' and keep asyncpg driver
clean_url = raw_url.split("?")[0]
config.set_main_option("sqlalchemy.url", clean_url)

target_metadata = SQLModel.metadata


def include_object(obj, name, type_, reflected, compare_to):
    if type_ == "table" and name.startswith("checkpoint"):
        return False
    return True


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        include_object=include_object,
        render_as_batch=True,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()