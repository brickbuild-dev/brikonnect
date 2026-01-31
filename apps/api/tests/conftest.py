from __future__ import annotations

import os
import socket

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app


def is_postgres_available() -> bool:
    """Check if Postgres is reachable on localhost:5432."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(("127.0.0.1", 5432))
        sock.close()
        return result == 0
    except Exception:
        return False


# Use SQLite if Postgres is not available (for CI/Codex environments without Docker)
if os.getenv("TEST_DATABASE_URL"):
    TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
elif is_postgres_available():
    TEST_DATABASE_URL = settings.DATABASE_URL
else:
    # Fallback to SQLite in-memory for tests
    TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
    print(f"⚠️  Postgres not available, using SQLite for tests")

# SQLite doesn't support pool_pre_ping
if TEST_DATABASE_URL.startswith("sqlite"):
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
else:
    engine = create_async_engine(TEST_DATABASE_URL, pool_pre_ping=True)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


@pytest.fixture(scope="session", autouse=True)
async def setup_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(autouse=True)
async def clean_database():
    async with AsyncSessionLocal() as session:
        for table in reversed(Base.metadata.sorted_tables):
            await session.execute(table.delete())
        await session.commit()
    yield


async def override_get_db():
    async with AsyncSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture()
async def db_session():
    async with AsyncSessionLocal() as session:
        yield session
