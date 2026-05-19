"""파일 업로드/서빙 테스트"""

import io
from datetime import UTC, datetime

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.common.id_generator import next_id
from app.core.security import create_access_token
from app.core.user.models import User
from tests.conftest import unique_email


async def _create_user(db: AsyncSession, user_level: int = 10) -> User:
    user_id = await next_id("USR_", db)
    now = datetime.now(UTC)
    user = User(
        id=user_id,
        email=unique_email(),
        name=f"유저_{user_id[-4:]}",
        user_level=user_level,
        joined_at=now,
        created_at=now,
        created_by=user_id,
        updated_at=now,
        updated_by=user_id,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest.mark.asyncio
async def test_upload_file(auth_client: AsyncClient, db: AsyncSession):
    """파일 업로드 → 201, FILE_ ID 발급"""
    user = await _create_user(db)
    token = create_access_token(user.id, user_level=10, user_name=user.name)
    auth_client.cookies.set("access_token", token)

    file_content = b"test file content"
    resp = await auth_client.post(
        "/api/v1/boards/translation/uploads",
        files={"file": ("test.jpg", io.BytesIO(file_content), "image/jpeg")},
    )
    assert resp.status_code == 201
    data = resp.json()["body"]["data"]
    assert data["file_id"].startswith("FILE_")
    assert data["file_ext"] == "jpg"
    assert data["file_size"] == len(file_content)


@pytest.mark.asyncio
async def test_upload_unauthenticated(auth_client: AsyncClient):
    """비로그인 파일 업로드 → 401"""
    resp = await auth_client.post(
        "/api/v1/boards/translation/uploads",
        files={"file": ("test.jpg", io.BytesIO(b"data"), "image/jpeg")},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_upload_board_not_found(auth_client: AsyncClient, db: AsyncSession):
    """없는 게시판 파일 업로드 → 404 BOARD_NOT_FOUND"""
    user = await _create_user(db)
    token = create_access_token(user.id, user_level=10, user_name=user.name)
    auth_client.cookies.set("access_token", token)

    resp = await auth_client.post(
        "/api/v1/boards/nonexistent/uploads",
        files={"file": ("test.jpg", io.BytesIO(b"data"), "image/jpeg")},
    )
    assert resp.status_code == 404
    assert resp.json()["header"]["code"] == "BOARD_NOT_FOUND"


# ---------------------------------------------------------------------------
# POST /api/v1/uploads — 공용 파일 업로드
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_general_upload_201(auth_client: AsyncClient, db: AsyncSession):
    """공용 파일 업로드 → 201, FILE_ ID 반환"""
    user = await _create_user(db)
    token = create_access_token(user.id, user_level=10, user_name=user.name)
    auth_client.cookies.set("access_token", token)

    resp = await auth_client.post(
        "/api/v1/uploads",
        files={"file": ("photo.png", io.BytesIO(b"\x89PNG\r\n\x1a\n"), "image/png")},
    )
    assert resp.status_code == 201
    data = resp.json()["body"]["data"]
    assert data["file_id"].startswith("FILE_")
    assert data["file_ext"] == "png"


@pytest.mark.asyncio
async def test_general_upload_unauthenticated(auth_client: AsyncClient):
    """미인증 공용 업로드 → 401"""
    resp = await auth_client.post(
        "/api/v1/uploads",
        files={"file": ("photo.png", io.BytesIO(b"data"), "image/png")},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_general_upload_size_exceeded(auth_client: AsyncClient, db: AsyncSession):
    """10MB 초과 파일 → 400 FILE_SIZE_EXCEEDED"""
    user = await _create_user(db)
    token = create_access_token(user.id, user_level=10, user_name=user.name)
    auth_client.cookies.set("access_token", token)

    oversized = b"x" * (10 * 1024 * 1024 + 1)
    resp = await auth_client.post(
        "/api/v1/uploads",
        files={"file": ("big.bin", io.BytesIO(oversized), "application/octet-stream")},
    )
    assert resp.status_code == 400
    assert resp.json()["header"]["code"] == "FILE_SIZE_EXCEEDED"
