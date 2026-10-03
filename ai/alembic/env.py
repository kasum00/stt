"""Alembic environment configured for an async SQLAlchemy application."""

from asyncio import run
from logging.config import fileConfig
import os
from pathlib import Path
import ssl
import sys

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env", override=False)
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from herstyle_ai.db.base import Base  # noqa: E402
from herstyle_ai.db import models  # noqa: E402,F401
from herstyle_ai.core.config import get_settings  # noqa: E402


config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def database_url() -> str:
    """Read the database URL from the environment, never from alembic.ini."""

    value = os.getenv("DATABASE_URL")
    if not value:
        raise RuntimeError("DATABASE_URL must be set before running Alembic.")
    return value


def run_migrations_offline() -> None:
    """Run migrations without creating a database connection."""

    context.configure(
        url=database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    """Configure Alembic on a synchronous connection proxy."""

    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Create an async engine and run the synchronous Alembic callbacks."""

    settings = get_settings()
    url = make_url(database_url())
    query = dict(url.query)
    ssl_mode = query.pop("sslmode", None) or settings.db_ssl_mode
    url = url.set(query=query)
    connect_args = {"timeout": settings.db_connect_timeout}
    if ssl_mode == "require":
        connect_args["ssl"] = "require"
    elif ssl_mode in {"verify-ca", "verify-full"}:
        ssl_context = ssl.create_default_context()
        if ssl_mode == "verify-ca":
            ssl_context.check_hostname = False
        connect_args["ssl"] = ssl_context
    elif ssl_mode not in {"disable", "off", "false"}:
        raise RuntimeError(
            "DB_SSL_MODE must be disable, require, verify-ca, or verify-full"
        )

    connectable = create_async_engine(
        url,
        poolclass=pool.NullPool,
        connect_args=connect_args,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations against the configured PostgreSQL database."""

    run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
