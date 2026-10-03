"""Async SQLAlchemy engine and request-scoped session dependency."""

from collections.abc import AsyncIterator
import ssl

from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from herstyle_ai.core.config import get_settings


def _ssl_connect_args(ssl_mode: str, ca_file: str | None = None) -> dict:
    mode = ssl_mode.strip().lower()
    if mode in {"disable", "off", "false"}:
        return {}
    if mode == "require":
        return {"ssl": "require"}
    if mode not in {"verify-ca", "verify-full"}:
        raise RuntimeError(
            "DB_SSL_MODE must be disable, require, verify-ca, or verify-full"
        )

    context = ssl.create_default_context(cafile=ca_file or None)
    if mode == "verify-ca":
        context.check_hostname = False
    return {"ssl": context}


def _build_engine():
    settings = get_settings()
    database_url = make_url(settings.database_url)

    # asyncpg expects ``ssl`` rather than libpq's ``sslmode``. Accept both
    # forms so managed-provider URLs work without provider-specific code.
    query = dict(database_url.query)
    url_ssl_mode = query.pop("sslmode", None)
    ssl_mode = url_ssl_mode or settings.db_ssl_mode
    database_url = database_url.set(query=query)

    connect_args = {
        "timeout": settings.db_connect_timeout,
        **_ssl_connect_args(ssl_mode),
    }

    return create_async_engine(
        database_url,
        pool_pre_ping=True,
        pool_use_lifo=True,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_timeout=settings.db_pool_timeout,
        pool_recycle=settings.db_pool_recycle,
        connect_args=connect_args,
    )


engine = _build_engine()

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncIterator[AsyncSession]:
    """Yield one request-scoped async database session."""

    async with AsyncSessionLocal() as session:
        yield session
