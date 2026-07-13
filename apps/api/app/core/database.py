"""Asynchronous database primitives owned by the API process."""

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import StaticPool


class Base(DeclarativeBase):
    """Declarative base shared by modular-monolith persistence models."""


def create_database(database_url: str) -> tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    """Create an async engine and transaction-scoped session factory."""
    options: dict[str, object] = {"pool_pre_ping": True}
    if database_url == "sqlite+aiosqlite://":
        options["poolclass"] = StaticPool
    engine = create_async_engine(database_url, **options)
    return engine, async_sessionmaker(engine, expire_on_commit=False)
