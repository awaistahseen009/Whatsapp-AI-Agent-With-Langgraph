import asyncio
from logging.config import fileConfig
from alembic import op
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

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
database_url = Config.DATABASE_URL
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option("sqlalchemy.url", database_url)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = SQLModel.metadata


def include_object(object, name, type_, reflected, compare_to):
    if type_ == "table" and name.startswith("checkpoint"):
        return False
    return True


def process_revision_directives(context, revision, directives):
    """
    Force create_type=False on all PostgreSQL ENUM columns in migration operations.
    This prevents SQLAlchemy from automatically emitting CREATE TYPE during
    table creation, which would conflict with explicit enum creation.
    """
    from sqlalchemy.dialects.postgresql import ENUM

    for directive in directives:
        if isinstance(directive, op.CreateTableOp):
            for column in directive.columns:
                if isinstance(column.type, ENUM):
                    column.type.create_type = False
        # Also handle AddColumnOp if needed (though your table creation is the main issue)
        elif isinstance(directive, op.AddColumnOp):
            if isinstance(directive.column.type, ENUM):
                directive.column.type.create_type = False


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
        render_as_batch=True,
        process_revision_directives=process_revision_directives,  # <-- ADDED
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        include_object=include_object,
        render_as_batch=True,
        process_revision_directives=process_revision_directives,  # <-- ADDED
    )

    with context.begin_transaction():
        # Pre-create any PostgreSQL enum types from metadata.
        # This ensures that any enum referenced by models exists before
        # the migration runs (idempotent due to checkfirst=True).
        # It does NOT interfere with your explicit enum creation in the migration
        # because checkfirst=True prevents duplicates.
        from sqlalchemy import Enum as SAEnum
        for table in target_metadata.sorted_tables:
            for col in table.columns:
                if isinstance(col.type, SAEnum):
                    col.type.create(connection, checkfirst=True)
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in 'online' mode with an async engine."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()