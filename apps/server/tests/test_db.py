"""SFR-100: DB 연결 및 Alembic 마이그레이션 기반 검증"""

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_db_connection(db: AsyncSession) -> None:
    """DB 연결이 정상적으로 이루어지는지 확인"""
    result = await db.execute(text("SELECT 1"))
    assert result.scalar() == 1


@pytest.mark.asyncio
async def test_alembic_version_table_exists(db: AsyncSession) -> None:
    """Alembic upgrade head 이후 alembic_version 테이블이 존재하는지 확인"""
    result = await db.execute(
        text(
            "SELECT EXISTS ("
            "  SELECT FROM information_schema.tables"
            "  WHERE table_name = 'alembic_version'"
            ")"
        )
    )
    assert result.scalar() is True


@pytest.mark.asyncio
async def test_alembic_has_revision(db: AsyncSession) -> None:
    """alembic_version 테이블에 revision이 기록되어 있는지 확인"""
    result = await db.execute(text("SELECT version_num FROM alembic_version"))
    revision = result.scalar()
    assert revision is not None
    assert len(revision) > 0
