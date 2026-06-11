import uuid
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING

import pytest_asyncio
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.config import settings
from app.db.session import get_db
from app.main import app

if TYPE_CHECKING:
    from httpx import AsyncClient


def _make_engine() -> AsyncEngine:
    return create_async_engine(settings.database_url, poolclass=NullPool)


@pytest_asyncio.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    """테스트용 DB 세션 — NullPool로 이벤트 루프 충돌 방지"""
    engine = _make_engine()
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session
    await engine.dispose()


@pytest_asyncio.fixture
async def auth_client(db: AsyncSession) -> AsyncGenerator["AsyncClient", None]:
    """테스트용 HTTP 클라이언트 — 앱의 get_db를 테스트 세션으로 오버라이드"""
    from httpx import ASGITransport, AsyncClient

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


def unique_email() -> str:
    """테스트마다 고유한 이메일 생성"""
    return f"test-{uuid.uuid4().hex[:8]}@example.com"
