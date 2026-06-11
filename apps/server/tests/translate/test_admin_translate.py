"""관리자 번역 이력 API 테스트"""

import tempfile
import uuid
from datetime import UTC, datetime, timedelta
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


async def _create_user(
    db: AsyncSession,
    *,
    user_level: int = 10,
    name: str = "테스트유저",
    use_yn: bool = True,
    block_yn: bool = False,
) -> User:
    user_id = await next_id("USR_", db)
    now = datetime.now(UTC)
    user = User(
        id=user_id,
        email=unique_email(),
        name=name,
        user_level=user_level,
        use_yn=use_yn,
        block_yn=block_yn,
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


async def _create_file(db: AsyncSession, owner_id: str, local_path: str) -> File:
    file_id = await next_id("FILE_", db)
    file_uuid = str(uuid.uuid4())
    now = datetime.now(UTC)
    file = File(
        id=file_id,
        uuid=file_uuid,
        original_name="source.png",
        stored_name="source.png",
        url_path=f"/files/{file_uuid}",
        local_path=local_path,
        file_size=1024,
        file_ext="png",
        mime_type="image/png",
        upload_type="API",
        created_at=now,
        created_by=owner_id,
        updated_at=now,
        updated_by=owner_id,
    )
    db.add(file)
    await db.commit()
    await db.refresh(file)
    return file


async def _create_book(
    db: AsyncSession,
    owner: User,
    *,
    status: str = "FAILED",
    title: str = "고문서 번역",
    source_file: File | None = None,
    created_at: datetime | None = None,
) -> Book:
    now = created_at or datetime.now(UTC)
    book = Book(
        id=await next_id("BOOK_", db),
        owner_user_id=owner.id,
        source_file_id=source_file.id if source_file else None,
        title=title,
        book_type="QUICK",
        source_type="IMAGE",
        total_pages=1,
        status=status,
        created_at=now,
        created_by=owner.id,
        updated_at=now,
        updated_by=owner.id,
    )
    db.add(book)
    await db.flush()
    page = BookPage(
        id=await next_id("BPAGE_", db),
        book_id=book.id,
        page_no=1,
        ocr_text="春望",
        literal_text="직역",
        interpretive_text="의역",
        ocr_engine="GOOGLE_VISION",
        translator_engine="GEMINI",
        status=status,
        created_at=now,
        created_by=owner.id,
        updated_at=now,
        updated_by=owner.id,
    )
    db.add(page)
    await db.commit()
    await db.refresh(book)
    return book


async def _create_run(
    db: AsyncSession,
    book_id: str,
    user_id: str,
    *,
    status: str = "FAILED",
    error_msg: str | None = "번역 실패",
    created_at: datetime | None = None,
) -> PipelineRun:
    run = PipelineRun(
        trigger_type="TRANSLATOR",
        triggered_by=user_id,
        book_id=book_id,
        status=status,
        error_msg=error_msg,
        created_at=created_at or datetime.now(UTC),
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)
    return run


def _set_token(client: AsyncClient, user: User) -> None:
    token = create_access_token(user.id, user_level=user.user_level, user_name=user.name)
    client.cookies.set("access_token", token)


@pytest.mark.asyncio
async def test_admin_list_translations_success(auth_client: AsyncClient, db: AsyncSession) -> None:
    admin = await _create_user(db, user_level=70, name="관리자")
    owner_name = f"번역소유자_{uuid.uuid4().hex[:8]}"
    owner = await _create_user(db, name=owner_name)
    book = await _create_book(db, owner, title="춘망 번역")
    await _create_run(db, book.id, owner.id, status="FAILED", error_msg="Gemini 오류")
    _set_token(auth_client, admin)

    response = await auth_client.post(
        "/admin/api/v1/translations/list",
        json={"page": 1, "size": 10, "keyword": owner_name, "status": "all"},
    )

    assert response.status_code == 200
    data = response.json()["body"]["data"]
    assert data["total"] == 1
    assert data["items"][0]["title"] == "춘망 번역"
    assert data["items"][0]["owner_name"] == owner_name
    assert data["items"][0]["owner_is_self"] is False
    assert data["items"][0]["latest_run_status"] == "FAILED"
    assert data["items"][0]["latest_run_error_msg"] == "Gemini 오류"


@pytest.mark.asyncio
async def test_admin_list_translations_forbidden_for_user(
    auth_client: AsyncClient, db: AsyncSession
) -> None:
    user = await _create_user(db, user_level=10)
    _set_token(auth_client, user)

    response = await auth_client.post(
        "/admin/api/v1/translations/list",
        json={"page": 1, "size": 10, "status": "all"},
    )

    assert response.status_code == 403
    assert response.json()["header"]["code"] == "FORBIDDEN"


@pytest.mark.asyncio
async def test_admin_list_translations_rejects_disabled_admin(
    auth_client: AsyncClient, db: AsyncSession
) -> None:
    admin = await _create_user(db, user_level=70, use_yn=False)
    _set_token(auth_client, admin)

    response = await auth_client.post(
        "/admin/api/v1/translations/list",
        json={"page": 1, "size": 10, "status": "all"},
    )

    assert response.status_code == 403
    assert response.json()["header"]["code"] == "ACCOUNT_DISABLED"


@pytest.mark.asyncio
async def test_admin_list_translations_rejects_blocked_admin(
    auth_client: AsyncClient, db: AsyncSession
) -> None:
    admin = await _create_user(db, user_level=70, block_yn=True)
    _set_token(auth_client, admin)

    response = await auth_client.post(
        "/admin/api/v1/translations/list",
        json={"page": 1, "size": 10, "status": "all"},
    )

    assert response.status_code == 403
    assert response.json()["header"]["code"] == "ACCOUNT_BLOCKED"


@pytest.mark.asyncio
async def test_admin_list_translations_filters_status(
    auth_client: AsyncClient, db: AsyncSession
) -> None:
    admin = await _create_user(db, user_level=70)
    owner_name = f"상태필터소유자_{uuid.uuid4().hex[:8]}"
    owner = await _create_user(db, name=owner_name)
    await _create_book(db, owner, status="FAILED", title="실패 번역")
    await _create_book(db, owner, status="COMPLETED", title="완료 번역")
    _set_token(auth_client, admin)

    response = await auth_client.post(
        "/admin/api/v1/translations/list",
        json={"page": 1, "size": 10, "keyword": owner_name, "status": "COMPLETED"},
    )

    assert response.status_code == 200
    data = response.json()["body"]["data"]
    assert data["total"] == 1
    assert data["items"][0]["title"] == "완료 번역"


@pytest.mark.asyncio
async def test_admin_list_translations_marks_self_owner(
    auth_client: AsyncClient, db: AsyncSession
) -> None:
    admin = await _create_user(db, user_level=70, name="본인관리자")
    title = f"내 번역_{uuid.uuid4().hex[:8]}"
    book = await _create_book(db, admin, title=title)
    _set_token(auth_client, admin)

    response = await auth_client.post(
        "/admin/api/v1/translations/list",
        json={"page": 1, "size": 10, "keyword": title, "status": "all"},
    )

    assert response.status_code == 200
    data = response.json()["body"]["data"]
    assert data["total"] == 1
    assert data["items"][0]["book_id"] == book.id
    assert data["items"][0]["owner_name"] == "본인관리자"
    assert data["items"][0]["owner_is_self"] is True


@pytest.mark.asyncio
async def test_admin_get_translation_includes_pages_and_runs(
    auth_client: AsyncClient, db: AsyncSession
) -> None:
    admin = await _create_user(db, user_level=70)
    owner = await _create_user(db, name="소유자")
    file = await _create_file(db, owner.id, "/tmp/source.png")
    book = await _create_book(db, owner, source_file=file)
    old_time = datetime.now(UTC) - timedelta(minutes=10)
    await _create_run(db, book.id, owner.id, status="RUNNING", created_at=old_time)
    latest = await _create_run(db, book.id, owner.id, status="FAILED", error_msg="최신 오류")
    _set_token(auth_client, admin)

    response = await auth_client.get(f"/admin/api/v1/translations/{book.id}")

    assert response.status_code == 200
    data = response.json()["body"]["data"]
    assert data["book_id"] == book.id
    assert data["owner_name"] == "소유자"
    assert data["owner_is_self"] is False
    assert data["source_file_url"].startswith("/files/")
    assert data["pages"][0]["has_ocr_text"] is True
    assert data["pages"][0]["ocr_text"] == "春望"
    assert data["pages"][0]["literal_text"] == "직역"
    assert data["pages"][0]["interpretive_text"] == "의역"
    assert data["pipeline_runs"][0]["id"] == latest.id
    assert data["pipeline_runs"][0]["error_msg"] == "최신 오류"
    assert "error_stack" not in data["pipeline_runs"][0]


@pytest.mark.asyncio
async def test_admin_retry_translation_success(auth_client: AsyncClient, db: AsyncSession) -> None:
    admin = await _create_user(db, user_level=70)
    owner = await _create_user(db)
    tmp = tempfile.mktemp(suffix=".png")
    Path(tmp).write_bytes(b"\x89PNG\r\n\x1a\n")
    file = await _create_file(db, owner.id, tmp)
    book = await _create_book(db, owner, source_file=file)
    _set_token(auth_client, admin)

    with patch("app.translate.service.run_pipeline", new=AsyncMock()) as run_pipeline:
        response = await auth_client.put(f"/admin/api/v1/translations/{book.id}/retry")

    assert response.status_code == 202
    data = response.json()["body"]["data"]
    assert data["book_id"] == book.id
    assert data["status"] == "PENDING"
    await db.refresh(book)
    assert book.status == "PENDING"
    run_pipeline.assert_awaited_once()
    Path(tmp).unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_admin_retry_translation_rejects_not_failed(
    auth_client: AsyncClient, db: AsyncSession
) -> None:
    admin = await _create_user(db, user_level=70)
    owner = await _create_user(db)
    book = await _create_book(db, owner, status="COMPLETED")
    _set_token(auth_client, admin)

    response = await auth_client.put(f"/admin/api/v1/translations/{book.id}/retry")

    assert response.status_code == 409
    assert response.json()["header"]["code"] == "BOOK_NOT_FAILED"


@pytest.mark.asyncio
async def test_admin_retry_translation_rejects_missing_source_file(
    auth_client: AsyncClient, db: AsyncSession
) -> None:
    admin = await _create_user(db, user_level=70)
    owner = await _create_user(db)
    book = await _create_book(db, owner, status="FAILED", source_file=None)
    _set_token(auth_client, admin)

    response = await auth_client.put(f"/admin/api/v1/translations/{book.id}/retry")

    assert response.status_code == 409
    assert response.json()["header"]["code"] == "BOOK_SOURCE_FILE_MISSING"
