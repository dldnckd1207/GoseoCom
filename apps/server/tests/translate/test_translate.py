"""SFR-106: 고서 번역기 테스트"""

import tempfile
import uuid
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.common.id_generator import next_id
from app.core.files.models import File
from app.core.security import create_access_token
from app.core.user.models import User
from app.translate.models import Book, BookPage, PipelineRun
from tests.conftest import unique_email

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _create_user(db: AsyncSession, user_level: int = 10) -> User:
    user_id = await next_id("USR_", db)
    now = datetime.now(UTC)
    user = User(
        id=user_id,
        email=unique_email(),
        name=f"테스트유저_{user_id[-4:]}",
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


async def _create_file(
    db: AsyncSession,
    owner_id: str,
    mime_type: str = "image/png",
    file_size: int = 1024,
    local_path: str = "/tmp/test.png",
) -> File:
    file_id = await next_id("FILE_", db)
    file_uuid = str(uuid.uuid4())
    now = datetime.now(UTC)
    file_entity = File(
        id=file_id,
        uuid=file_uuid,
        original_name="test.png",
        stored_name=f"{file_uuid}.png",
        url_path=f"/files/{file_uuid}",
        local_path=local_path,
        file_size=file_size,
        file_ext="png",
        mime_type=mime_type,
        upload_type="API",
        created_at=now,
        created_by=owner_id,
        updated_at=now,
        updated_by=owner_id,
    )
    db.add(file_entity)
    await db.commit()
    await db.refresh(file_entity)
    return file_entity


async def _create_book_with_page(
    db: AsyncSession, owner_id: str
) -> tuple[Book, BookPage, PipelineRun]:
    now = datetime.now(UTC)
    book = Book(
        id=await next_id("BOOK_", db),
        owner_user_id=owner_id,
        title="test.png",
        book_type="QUICK",
        source_type="IMAGE",
        total_pages=1,
        status="PENDING",
        created_at=now,
        created_by=owner_id,
        updated_at=now,
        updated_by=owner_id,
    )
    db.add(book)
    await db.flush()

    page = BookPage(
        id=await next_id("BPAGE_", db),
        book_id=book.id,
        page_no=1,
        status="PENDING",
        created_at=now,
        created_by=owner_id,
        updated_at=now,
        updated_by=owner_id,
    )
    db.add(page)

    run = PipelineRun(
        trigger_type="TRANSLATOR",
        triggered_by=owner_id,
        book_id=book.id,
        status="PENDING",
        created_at=now,
    )
    db.add(run)
    await db.commit()
    await db.refresh(book)
    await db.refresh(page)
    await db.refresh(run)
    return book, page, run


# ---------------------------------------------------------------------------
# Pipeline 단위 테스트 — AsyncSessionLocal을 테스트 세션으로 대체
# ---------------------------------------------------------------------------


class _MockSessionFactory:
    """runner의 `async with AsyncSessionLocal() as db:` 를 테스트 세션으로 교체"""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    def __call__(self) -> "_MockSessionFactory":
        return self

    async def __aenter__(self) -> AsyncSession:
        return self._db

    async def __aexit__(self, *_: object) -> None:
        pass


@pytest.mark.asyncio
async def test_pipeline_completed(db: AsyncSession) -> None:
    """정상 흐름: OCR → 번역 → COMPLETED"""
    from app.translate.pipeline.runner import run_pipeline

    user = await _create_user(db)
    book, page, run = await _create_book_with_page(db, user.id)

    tmp = tempfile.mktemp(suffix=".png")
    Path(tmp).write_bytes(b"\x89PNG\r\n\x1a\n")

    with (
        patch("app.translate.pipeline.runner.AsyncSessionLocal", _MockSessionFactory(db)),
        patch(
            "app.translate.pipeline.runner.run_ocr", new=AsyncMock(return_value="春望 國破山河在")
        ),
        patch(
            "app.translate.pipeline.runner.run_translate",
            new=AsyncMock(return_value=("직역 결과", "의역 결과")),
        ),
    ):
        await run_pipeline(book.id, tmp, run.id)

    await db.refresh(book)
    await db.refresh(page)
    await db.refresh(run)

    assert book.status == "COMPLETED"
    assert page.status == "COMPLETED"
    assert page.ocr_text == "春望 國破山河在"
    assert page.literal_text == "직역 결과"
    assert page.interpretive_text == "의역 결과"
    assert run.status == "COMPLETED"
    assert run.success_cnt == 1
    Path(tmp).unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_pipeline_no_text(db: AsyncSession) -> None:
    """OCR 텍스트 없음 → COMPLETED + page.status = NO_TEXT"""
    from app.translate.pipeline.runner import run_pipeline

    user = await _create_user(db)
    book, page, run = await _create_book_with_page(db, user.id)
    tmp = tempfile.mktemp(suffix=".png")
    Path(tmp).write_bytes(b"\x89PNG\r\n\x1a\n")

    with (
        patch("app.translate.pipeline.runner.AsyncSessionLocal", _MockSessionFactory(db)),
        patch("app.translate.pipeline.runner.run_ocr", new=AsyncMock(return_value="")),
    ):
        await run_pipeline(book.id, tmp, run.id)

    await db.refresh(book)
    await db.refresh(page)
    await db.refresh(run)

    assert book.status == "COMPLETED"
    assert page.status == "NO_TEXT"
    assert page.updated_by is not None
    assert run.status == "COMPLETED"
    Path(tmp).unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_pipeline_ocr_failure(db: AsyncSession) -> None:
    """OCR 예외 → FAILED"""
    from app.translate.pipeline.runner import run_pipeline

    user = await _create_user(db)
    book, page, run = await _create_book_with_page(db, user.id)
    tmp = tempfile.mktemp(suffix=".png")
    Path(tmp).write_bytes(b"\x89PNG\r\n\x1a\n")

    with (
        patch("app.translate.pipeline.runner.AsyncSessionLocal", _MockSessionFactory(db)),
        patch(
            "app.translate.pipeline.runner.run_ocr",
            new=AsyncMock(side_effect=RuntimeError("Vision API 오류")),
        ),
    ):
        await run_pipeline(book.id, tmp, run.id)

    await db.refresh(book)
    await db.refresh(run)

    assert book.status == "FAILED"
    assert run.status == "FAILED"
    assert run.fail_cnt == 1
    assert "Vision API 오류" in (run.error_msg or "")
    Path(tmp).unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_pipeline_translate_failure(db: AsyncSession) -> None:
    """번역 예외 → FAILED"""
    from app.translate.pipeline.runner import run_pipeline

    user = await _create_user(db)
    book, page, run = await _create_book_with_page(db, user.id)
    tmp = tempfile.mktemp(suffix=".png")
    Path(tmp).write_bytes(b"\x89PNG\r\n\x1a\n")

    with (
        patch("app.translate.pipeline.runner.AsyncSessionLocal", _MockSessionFactory(db)),
        patch("app.translate.pipeline.runner.run_ocr", new=AsyncMock(return_value="春望")),
        patch(
            "app.translate.pipeline.runner.run_translate",
            new=AsyncMock(side_effect=RuntimeError("Gemini 파싱 실패")),
        ),
    ):
        await run_pipeline(book.id, tmp, run.id)

    await db.refresh(book)
    await db.refresh(run)

    assert book.status == "FAILED"
    assert run.status == "FAILED"
    assert "Gemini 파싱 실패" in (run.error_msg or "")
    Path(tmp).unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# API 테스트
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_start_translate_202(auth_client: AsyncClient, db: AsyncSession) -> None:
    """file_id로 번역 시작 → 202, book_id 반환"""
    user = await _create_user(db)
    file_entity = await _create_file(db, user.id)
    token = create_access_token(user.id, user_level=10, user_name=user.name)
    auth_client.cookies.set("access_token", token)

    with patch("app.translate.service.run_pipeline", new=AsyncMock()):
        resp = await auth_client.post(
            "/api/v1/translate",
            json={"file_id": file_entity.id},
        )

    assert resp.status_code == 202
    data = resp.json()["body"]["data"]
    assert data["book_id"].startswith("BOOK_")
    assert data["status"] == "PENDING"


@pytest.mark.asyncio
async def test_start_translate_file_not_found(auth_client: AsyncClient, db: AsyncSession) -> None:
    """존재하지 않는 file_id → 404 FILE_NOT_FOUND"""
    user = await _create_user(db)
    token = create_access_token(user.id, user_level=10, user_name=user.name)
    auth_client.cookies.set("access_token", token)

    resp = await auth_client.post(
        "/api/v1/translate",
        json={"file_id": "FILE_99999999"},
    )

    assert resp.status_code == 404
    assert resp.json()["header"]["code"] == "FILE_NOT_FOUND"


@pytest.mark.asyncio
async def test_start_translate_file_forbidden(auth_client: AsyncClient, db: AsyncSession) -> None:
    """타인 file_id로 번역 요청 → 403 FILE_ACCESS_FORBIDDEN"""
    owner = await _create_user(db)
    other = await _create_user(db)
    file_entity = await _create_file(db, owner.id)

    token = create_access_token(other.id, user_level=10, user_name=other.name)
    auth_client.cookies.set("access_token", token)

    resp = await auth_client.post(
        "/api/v1/translate",
        json={"file_id": file_entity.id},
    )

    assert resp.status_code == 403
    assert resp.json()["header"]["code"] == "FILE_ACCESS_FORBIDDEN"


@pytest.mark.asyncio
async def test_start_translate_invalid_image_type(
    auth_client: AsyncClient, db: AsyncSession
) -> None:
    """이미지 아닌 파일 → 400 INVALID_IMAGE_TYPE"""
    user = await _create_user(db)
    file_entity = await _create_file(db, user.id, mime_type="application/pdf")
    token = create_access_token(user.id, user_level=10, user_name=user.name)
    auth_client.cookies.set("access_token", token)

    resp = await auth_client.post(
        "/api/v1/translate",
        json={"file_id": file_entity.id},
    )

    assert resp.status_code == 400
    assert resp.json()["header"]["code"] == "INVALID_IMAGE_TYPE"


@pytest.mark.asyncio
async def test_start_translate_size_exceeded(auth_client: AsyncClient, db: AsyncSession) -> None:
    """10MB 초과 파일 → 400 IMAGE_SIZE_EXCEEDED"""
    user = await _create_user(db)
    file_entity = await _create_file(db, user.id, file_size=11 * 1024 * 1024)
    token = create_access_token(user.id, user_level=10, user_name=user.name)
    auth_client.cookies.set("access_token", token)

    resp = await auth_client.post(
        "/api/v1/translate",
        json={"file_id": file_entity.id},
    )

    assert resp.status_code == 400
    assert resp.json()["header"]["code"] == "IMAGE_SIZE_EXCEEDED"


@pytest.mark.asyncio
async def test_start_translate_unauthenticated(auth_client: AsyncClient) -> None:
    """미인증 → 401"""
    resp = await auth_client.post(
        "/api/v1/translate",
        json={"file_id": "FILE_00000001"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_book_forbidden(auth_client: AsyncClient, db: AsyncSession) -> None:
    """타인 book_id 조회 → 403"""
    owner = await _create_user(db)
    other = await _create_user(db)
    book, _, _ = await _create_book_with_page(db, owner.id)

    token = create_access_token(other.id, user_level=10, user_name=other.name)
    auth_client.cookies.set("access_token", token)

    resp = await auth_client.get(f"/api/v1/translate/{book.id}")
    assert resp.status_code == 403
    assert resp.json()["header"]["code"] == "FORBIDDEN"


@pytest.mark.asyncio
async def test_get_book_not_found(auth_client: AsyncClient, db: AsyncSession) -> None:
    """존재하지 않는 book_id → 404"""
    user = await _create_user(db)
    token = create_access_token(user.id, user_level=10, user_name=user.name)
    auth_client.cookies.set("access_token", token)

    resp = await auth_client.get("/api/v1/translate/BOOK_99999999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_book_owner(auth_client: AsyncClient, db: AsyncSession) -> None:
    """본인 book_id 조회 → 200"""
    user = await _create_user(db)
    book, _, _ = await _create_book_with_page(db, user.id)
    token = create_access_token(user.id, user_level=10, user_name=user.name)
    auth_client.cookies.set("access_token", token)

    resp = await auth_client.get(f"/api/v1/translate/{book.id}")
    assert resp.status_code == 200
    data = resp.json()["body"]["data"]
    assert data["book_id"] == book.id
    assert len(data["pages"]) == 1


@pytest.mark.asyncio
async def test_list_books(auth_client: AsyncClient, db: AsyncSession) -> None:
    """내 번역 목록 → 본인 데이터만 반환"""
    user = await _create_user(db)
    other = await _create_user(db)
    await _create_book_with_page(db, user.id)
    await _create_book_with_page(db, other.id)

    token = create_access_token(user.id, user_level=10, user_name=user.name)
    auth_client.cookies.set("access_token", token)

    resp = await auth_client.post("/api/v1/translate/list", json={"page": 1, "size": 10})
    assert resp.status_code == 200
    data = resp.json()["body"]["data"]
    assert data["total"] >= 1
    for item in data["items"]:
        assert item["book_id"].startswith("BOOK_")


@pytest.mark.asyncio
async def test_list_books_status_filter(auth_client: AsyncClient, db: AsyncSession) -> None:
    """status 필터 → 해당 status만 반환"""
    user = await _create_user(db)
    await _create_book_with_page(db, user.id)
    token = create_access_token(user.id, user_level=10, user_name=user.name)
    auth_client.cookies.set("access_token", token)

    resp = await auth_client.post(
        "/api/v1/translate/list",
        json={"page": 1, "size": 10, "status": "COMPLETED"},
    )
    assert resp.status_code == 200
    for item in resp.json()["body"]["data"]["items"]:
        assert item["status"] == "COMPLETED"


@pytest.mark.asyncio
async def test_list_books_invalid_status(auth_client: AsyncClient, db: AsyncSession) -> None:
    """허용되지 않는 status → 422"""
    user = await _create_user(db)
    token = create_access_token(user.id, user_level=10, user_name=user.name)
    auth_client.cookies.set("access_token", token)

    resp = await auth_client.post(
        "/api/v1/translate/list",
        json={"status": "INVALID_STATUS"},
    )
    assert resp.status_code == 422
