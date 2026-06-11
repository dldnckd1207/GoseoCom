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
    book, _page, run = await _create_book_with_page(db, user.id)
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
    book, _page, run = await _create_book_with_page(db, user.id)
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


# ---------------------------------------------------------------------------
# SFR-206: 즐겨찾기 토글 + 필터, 제목 검색
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_toggle_favorite_on(auth_client: AsyncClient, db: AsyncSession) -> None:
    """즐겨찾기 토글 ON → is_favorite=True"""
    user = await _create_user(db)
    book, _, _ = await _create_book_with_page(db, user.id)
    token = create_access_token(user.id, user_level=10, user_name=user.name)
    auth_client.cookies.set("access_token", token)

    resp = await auth_client.put(f"/api/v1/translate/{book.id}/favorite")
    assert resp.status_code == 200
    data = resp.json()["body"]["data"]
    assert data["book_id"] == book.id
    assert data["is_favorite"] is True


@pytest.mark.asyncio
async def test_toggle_favorite_off(auth_client: AsyncClient, db: AsyncSession) -> None:
    """즐겨찾기 두 번 토글 → is_favorite=False"""
    user = await _create_user(db)
    book, _, _ = await _create_book_with_page(db, user.id)
    token = create_access_token(user.id, user_level=10, user_name=user.name)
    auth_client.cookies.set("access_token", token)

    await auth_client.put(f"/api/v1/translate/{book.id}/favorite")
    resp = await auth_client.put(f"/api/v1/translate/{book.id}/favorite")
    assert resp.status_code == 200
    assert resp.json()["body"]["data"]["is_favorite"] is False


@pytest.mark.asyncio
async def test_toggle_favorite_forbidden(auth_client: AsyncClient, db: AsyncSession) -> None:
    """타인 book 즐겨찾기 → 403"""
    owner = await _create_user(db)
    other = await _create_user(db)
    book, _, _ = await _create_book_with_page(db, owner.id)

    token = create_access_token(other.id, user_level=10, user_name=other.name)
    auth_client.cookies.set("access_token", token)

    resp = await auth_client.put(f"/api/v1/translate/{book.id}/favorite")
    assert resp.status_code == 403
    assert resp.json()["header"]["code"] == "FORBIDDEN"


@pytest.mark.asyncio
async def test_toggle_favorite_not_found(auth_client: AsyncClient, db: AsyncSession) -> None:
    """존재하지 않는 book 즐겨찾기 → 404"""
    user = await _create_user(db)
    token = create_access_token(user.id, user_level=10, user_name=user.name)
    auth_client.cookies.set("access_token", token)

    resp = await auth_client.put("/api/v1/translate/BOOK_99999999/favorite")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_books_favorite_filter(auth_client: AsyncClient, db: AsyncSession) -> None:
    """is_favorite=true 필터 → 즐겨찾기만 반환"""
    user = await _create_user(db)
    book_fav, _, _ = await _create_book_with_page(db, user.id)
    await _create_book_with_page(db, user.id)

    token = create_access_token(user.id, user_level=10, user_name=user.name)
    auth_client.cookies.set("access_token", token)

    await auth_client.put(f"/api/v1/translate/{book_fav.id}/favorite")

    resp = await auth_client.post(
        "/api/v1/translate/list",
        json={"page": 1, "size": 10, "is_favorite": True},
    )
    assert resp.status_code == 200
    items = resp.json()["body"]["data"]["items"]
    assert len(items) >= 1
    assert all(item["is_favorite"] is True for item in items)


@pytest.mark.asyncio
async def test_list_books_title_search(auth_client: AsyncClient, db: AsyncSession) -> None:
    """q 검색 → 제목 포함 항목만 반환"""
    user = await _create_user(db)
    book, _, _ = await _create_book_with_page(db, user.id)

    token = create_access_token(user.id, user_level=10, user_name=user.name)
    auth_client.cookies.set("access_token", token)

    await auth_client.put(
        f"/api/v1/translate/{book.id}",
        json={"title": "조선왕조실록 1페이지"},
    )

    resp = await auth_client.post(
        "/api/v1/translate/list",
        json={"page": 1, "size": 10, "q": "조선왕조"},
    )
    assert resp.status_code == 200
    items = resp.json()["body"]["data"]["items"]
    assert any("조선왕조" in item["title"] for item in items)


@pytest.mark.asyncio
async def test_list_books_title_search_no_result(
    auth_client: AsyncClient, db: AsyncSession
) -> None:
    """q 검색 — 매칭 없으면 빈 결과"""
    user = await _create_user(db)
    token = create_access_token(user.id, user_level=10, user_name=user.name)
    auth_client.cookies.set("access_token", token)

    resp = await auth_client.post(
        "/api/v1/translate/list",
        json={"page": 1, "size": 10, "q": "절대로존재하지않을제목xyz"},
    )
    assert resp.status_code == 200
    assert resp.json()["body"]["data"]["total"] == 0


@pytest.mark.asyncio
async def test_list_books_combined_filter(auth_client: AsyncClient, db: AsyncSession) -> None:
    """is_favorite + q 조합 필터"""
    user = await _create_user(db)
    book, _, _ = await _create_book_with_page(db, user.id)

    token = create_access_token(user.id, user_level=10, user_name=user.name)
    auth_client.cookies.set("access_token", token)

    await auth_client.put(
        f"/api/v1/translate/{book.id}",
        json={"title": "고려사 1권"},
    )
    await auth_client.put(f"/api/v1/translate/{book.id}/favorite")

    resp = await auth_client.post(
        "/api/v1/translate/list",
        json={"page": 1, "size": 10, "is_favorite": True, "q": "고려사"},
    )
    assert resp.status_code == 200
    items = resp.json()["body"]["data"]["items"]
    assert any(item["is_favorite"] and "고려사" in item["title"] for item in items)


# ---------------------------------------------------------------------------
# library-search-bookmark: 공개 목록 검색 + 북마크
# ---------------------------------------------------------------------------


async def _create_completed_book(db: AsyncSession, owner_id: str, title: str = "test.png") -> Book:
    """COMPLETED 상태의 공개 Book 생성"""
    now = datetime.now(UTC)
    book = Book(
        id=await next_id("BOOK_", db),
        owner_user_id=owner_id,
        title=title,
        book_type="QUICK",
        source_type="IMAGE",
        total_pages=1,
        status="COMPLETED",
        created_at=now,
        created_by=owner_id,
        updated_at=now,
        updated_by=owner_id,
    )
    db.add(book)
    await db.commit()
    await db.refresh(book)
    return book


@pytest.mark.asyncio
async def test_list_public_books_no_auth(auth_client: AsyncClient, db: AsyncSession) -> None:
    """비로그인 공개 목록 조회 → is_bookmarked=False"""
    owner = await _create_user(db)
    await _create_completed_book(db, owner.id, "공개번역")

    resp = await auth_client.post("/api/v1/translate/public/list", json={"page": 1, "size": 12})
    assert resp.status_code == 200
    items = resp.json()["body"]["data"]["items"]
    assert all(item["is_bookmarked"] is False for item in items)


@pytest.mark.asyncio
async def test_list_public_books_q_search(auth_client: AsyncClient, db: AsyncSession) -> None:
    """q 검색 → 제목 포함 항목만 반환"""
    owner = await _create_user(db)
    await _create_completed_book(db, owner.id, "조선왕조실록 1권")
    await _create_completed_book(db, owner.id, "고려사 개요")

    resp = await auth_client.post(
        "/api/v1/translate/public/list",
        json={"page": 1, "size": 12, "q": "조선왕조"},
    )
    assert resp.status_code == 200
    items = resp.json()["body"]["data"]["items"]
    assert all("조선왕조" in item["title"] for item in items)


@pytest.mark.asyncio
async def test_toggle_bookmark_on(auth_client: AsyncClient, db: AsyncSession) -> None:
    """북마크 ON → is_bookmarked=True"""
    owner = await _create_user(db)
    user = await _create_user(db)
    book = await _create_completed_book(db, owner.id)

    token = create_access_token(user.id, user_level=10, user_name=user.name)
    auth_client.cookies.set("access_token", token)

    resp = await auth_client.put(f"/api/v1/translate/public/{book.id}/bookmark")
    assert resp.status_code == 200
    data = resp.json()["body"]["data"]
    assert data["book_id"] == book.id
    assert data["is_bookmarked"] is True


@pytest.mark.asyncio
async def test_toggle_bookmark_off(auth_client: AsyncClient, db: AsyncSession) -> None:
    """북마크 두 번 → is_bookmarked=False"""
    owner = await _create_user(db)
    user = await _create_user(db)
    book = await _create_completed_book(db, owner.id)

    token = create_access_token(user.id, user_level=10, user_name=user.name)
    auth_client.cookies.set("access_token", token)

    await auth_client.put(f"/api/v1/translate/public/{book.id}/bookmark")
    resp = await auth_client.put(f"/api/v1/translate/public/{book.id}/bookmark")
    assert resp.status_code == 200
    assert resp.json()["body"]["data"]["is_bookmarked"] is False


@pytest.mark.asyncio
async def test_toggle_bookmark_own_book(auth_client: AsyncClient, db: AsyncSession) -> None:
    """본인 Book 북마크 → 400"""
    user = await _create_user(db)
    book = await _create_completed_book(db, user.id)

    token = create_access_token(user.id, user_level=10, user_name=user.name)
    auth_client.cookies.set("access_token", token)

    resp = await auth_client.put(f"/api/v1/translate/public/{book.id}/bookmark")
    assert resp.status_code == 400
    assert resp.json()["header"]["code"] == "CANNOT_BOOKMARK_OWN"


@pytest.mark.asyncio
async def test_toggle_bookmark_not_found(auth_client: AsyncClient, db: AsyncSession) -> None:
    """존재하지 않는 book → 404"""
    user = await _create_user(db)
    token = create_access_token(user.id, user_level=10, user_name=user.name)
    auth_client.cookies.set("access_token", token)

    resp = await auth_client.put("/api/v1/translate/public/BOOK_99999999/bookmark")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_toggle_bookmark_unauthenticated(auth_client: AsyncClient, db: AsyncSession) -> None:
    """비인증 북마크 → 401"""
    owner = await _create_user(db)
    book = await _create_completed_book(db, owner.id)

    resp = await auth_client.put(f"/api/v1/translate/public/{book.id}/bookmark")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_list_public_books_bm_filter(auth_client: AsyncClient, db: AsyncSession) -> None:
    """bm=True 필터 → 북마크한 항목만 반환, is_bookmarked=True"""
    owner = await _create_user(db)
    user = await _create_user(db)
    book_bm = await _create_completed_book(db, owner.id, "북마크할 책")
    await _create_completed_book(db, owner.id, "북마크 안 할 책")

    token = create_access_token(user.id, user_level=10, user_name=user.name)
    auth_client.cookies.set("access_token", token)

    await auth_client.put(f"/api/v1/translate/public/{book_bm.id}/bookmark")

    resp = await auth_client.post(
        "/api/v1/translate/public/list",
        json={"page": 1, "size": 12, "bm": True},
    )
    assert resp.status_code == 200
    items = resp.json()["body"]["data"]["items"]
    assert len(items) >= 1
    assert all(item["is_bookmarked"] is True for item in items)


@pytest.mark.asyncio
async def test_list_public_books_is_bookmarked_field(
    auth_client: AsyncClient, db: AsyncSession
) -> None:
    """로그인 후 북마크한 항목은 is_bookmarked=True, 안 한 항목은 False"""
    owner = await _create_user(db)
    user = await _create_user(db)
    book_bm = await _create_completed_book(db, owner.id, "북마크 책")
    await _create_completed_book(db, owner.id, "일반 책")

    token = create_access_token(user.id, user_level=10, user_name=user.name)
    auth_client.cookies.set("access_token", token)

    await auth_client.put(f"/api/v1/translate/public/{book_bm.id}/bookmark")

    resp = await auth_client.post(
        "/api/v1/translate/public/list",
        json={"page": 1, "size": 12},
    )
    assert resp.status_code == 200
    items = resp.json()["body"]["data"]["items"]
    bm_item = next((i for i in items if i["book_id"] == book_bm.id), None)
    assert bm_item is not None
    assert bm_item["is_bookmarked"] is True


# ---------------------------------------------------------------------------
# SFR-202: analyzer 테스트
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_run_analyze_basic() -> None:
    """run_analyze: Gemini mock → summary/keywords/count 반환 검증"""
    from unittest.mock import AsyncMock, MagicMock, patch

    from app.translate.pipeline.analyzer import run_analyze

    mock_response = MagicMock()
    mock_response.text = '{"summary": "조선시대 유배 기록", "keywords": [{"word": "流配", "reading": "유배", "meaning": "귀양 보냄"}, {"word": "謫所", "reading": "적소", "meaning": "귀양지"}]}'

    with (
        patch("app.translate.pipeline.analyzer.settings") as mock_settings,
        patch(
            "app.translate.pipeline.analyzer.asyncio.wait_for",
            new=AsyncMock(return_value=mock_response),
        ),
    ):
        mock_settings.gemini_api_key = "test-key"
        mock_settings.gemini_model = "gemini-2.5-flash"

        ocr_text = "流配謫所流配"
        summary, keywords = await run_analyze(ocr_text, "의역 결과")

    assert summary == "조선시대 유배 기록"
    assert len(keywords) == 2
    kw_liupei = next(kw for kw in keywords if kw["word"] == "流配")
    assert kw_liupei["reading"] == "유배"
    assert kw_liupei["count"] == 2  # OCR 원문에 2번 등장
    kw_jeokso = next(kw for kw in keywords if kw["word"] == "謫所")
    assert kw_jeokso["count"] == 1


@pytest.mark.asyncio
async def test_pipeline_analyzer_graceful_degradation(db: AsyncSession) -> None:
    """analyzer 예외 시 pipeline COMPLETED 유지, summary_text/keywords는 None"""
    from app.translate.pipeline.runner import run_pipeline

    user = await _create_user(db)
    book, _page, run = await _create_book_with_page(db, user.id)
    tmp = tempfile.mktemp(suffix=".png")
    Path(tmp).write_bytes(b"\x89PNG\r\n\x1a\n")

    with (
        patch("app.translate.pipeline.runner.AsyncSessionLocal", _MockSessionFactory(db)),
        patch(
            "app.translate.pipeline.runner.run_ocr", new=AsyncMock(return_value="春望 國破山河在")
        ),
        patch(
            "app.translate.pipeline.runner.run_translate",
            new=AsyncMock(return_value=("직역", "의역")),
        ),
        patch(
            "app.translate.pipeline.runner.run_analyze",
            new=AsyncMock(side_effect=RuntimeError("Gemini 타임아웃")),
        ),
    ):
        await run_pipeline(book.id, tmp, run.id)

    await db.refresh(book)
    await db.refresh(run)

    assert book.status == "COMPLETED"
    assert run.status == "COMPLETED"
    assert book.summary_text is None
    assert book.keywords is None
    Path(tmp).unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_translate_only_analyzer_called(db: AsyncSession) -> None:
    """run_translate_only도 analyzer 호출 → summary_text 저장"""
    from app.translate.pipeline.runner import run_translate_only

    user = await _create_user(db)
    book, page, run = await _create_book_with_page(db, user.id)

    page.ocr_text = "春望 國破山河在"
    await db.commit()

    with (
        patch("app.translate.pipeline.runner.AsyncSessionLocal", _MockSessionFactory(db)),
        patch(
            "app.translate.pipeline.runner.run_translate",
            new=AsyncMock(return_value=("직역", "의역")),
        ),
        patch(
            "app.translate.pipeline.runner.run_analyze",
            new=AsyncMock(
                return_value=(
                    "핵심 요약 결과",
                    [{"word": "春望", "reading": "춘망", "meaning": "봄의 희망", "count": 1}],
                )
            ),
        ),
    ):
        await run_translate_only(book.id, run.id)

    await db.refresh(book)

    assert book.status == "COMPLETED"
    assert book.summary_text == "핵심 요약 결과"
    assert isinstance(book.keywords, list)
    assert book.keywords[0]["word"] == "春望"


@pytest.mark.asyncio
async def test_get_book_includes_analyze_fields(auth_client: AsyncClient, db: AsyncSession) -> None:
    """GET /api/v1/translate/{id} 응답에 summary_text, keywords 포함"""
    user = await _create_user(db)
    book, _, _ = await _create_book_with_page(db, user.id)

    book.summary_text = "핵심 요약 테스트"
    book.keywords = [{"word": "流配", "reading": "유배", "meaning": "귀양", "count": 3}]
    await db.commit()

    token = create_access_token(user.id, user_level=10, user_name=user.name)
    auth_client.cookies.set("access_token", token)

    resp = await auth_client.get(f"/api/v1/translate/{book.id}")
    assert resp.status_code == 200
    data = resp.json()["body"]["data"]
    assert data["summary_text"] == "핵심 요약 테스트"
    assert isinstance(data["keywords"], list)
    assert data["keywords"][0]["word"] == "流配"
