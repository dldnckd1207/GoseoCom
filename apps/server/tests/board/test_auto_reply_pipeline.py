"""SFR-104 / SFR-205: AI 자동 답변 파이프라인 테스트"""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.board.auto_reply_pipeline import _find_eligible_posts, _process_post
from app.board.models import Board, Comment, Post
from app.config import settings
from app.core.common.id_generator import next_id
from app.core.files.models import File, FileMap
from app.core.user.models import User
from app.translate.models import Book, PipelineRun
from tests.conftest import unique_email

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _create_board(
    db: AsyncSession,
    *,
    auto_reply_enabled: bool = True,
    comment_yn: bool = True,
    auto_reply_delay_min: int = 0,
    pipeline_enabled: bool = False,
) -> Board:
    now = datetime.now(UTC)
    board = Board(
        id=await next_id("BRD_", db),
        board_code=f"ar_test_{uuid.uuid4().hex[:6]}",
        board_name="자동답변 테스트 게시판",
        board_type="LIST",
        read_yn=True,
        guest_read_yn=True,
        write_yn=True,
        guest_write_yn=False,
        notice_yn=False,
        reply_yn=False,
        comment_yn=comment_yn,
        secret_yn=False,
        like_yn=False,
        category_yn=False,
        attach_yn=False,
        attach_size=10240,
        attach_count=5,
        list_count=20,
        auto_reply_enabled=auto_reply_enabled,
        auto_reply_delay_min=auto_reply_delay_min,
        pipeline_enabled=pipeline_enabled,
        sort_order=99,
        use_yn=True,
        created_at=now,
        created_by=settings.ai_agent_user_id,
        updated_at=now,
        updated_by=settings.ai_agent_user_id,
    )
    db.add(board)
    await db.commit()
    await db.refresh(board)
    return board


async def _create_user(db: AsyncSession) -> User:
    now = datetime.now(UTC)
    user_id = await next_id("USR_", db)
    user = User(
        id=user_id,
        email=unique_email(),
        name=f"유저_{user_id[-4:]}",
        user_level=10,
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


async def _create_post(
    db: AsyncSession,
    board_id: str,
    user_id: str,
    *,
    auto_reply_status: str = "PENDING",
    comment_count: int = 0,
    del_yn: bool = False,
    created_at: datetime | None = None,
    book_id: str | None = None,
) -> Post:
    now = datetime.now(UTC)
    post = Post(
        id=await next_id("POST_", db),
        board_id=board_id,
        user_id=user_id,
        author_name="테스트유저",
        title="고서 해독 질문",
        content="이 고서의 내용을 해독해주세요.",
        auto_reply_status=auto_reply_status,
        comment_count=comment_count,
        del_yn=del_yn,
        book_id=book_id,
        created_at=created_at or now,
        created_by=user_id,
        updated_at=created_at or now,
        updated_by=user_id,
    )
    db.add(post)
    await db.commit()
    await db.refresh(post)
    return post


async def _create_book(db: AsyncSession, user_id: str) -> Book:
    now = datetime.now(UTC)
    book = Book(
        id=await next_id("BOOK_", db),
        owner_user_id=user_id,
        title="테스트 고서",
        book_type="QUICK",
        source_type="IMAGE",
        total_pages=1,
        status="COMPLETED",
        created_at=now,
        created_by=user_id,
        updated_at=now,
        updated_by=user_id,
    )
    db.add(book)
    await db.commit()
    await db.refresh(book)
    return book


async def _create_image_attachment(db: AsyncSession, post_id: str, user_id: str) -> File:
    """게시글에 이미지 파일 첨부 픽스처 생성."""
    now = datetime.now(UTC)
    file = File(
        id=await next_id("FILE_", db),
        uuid=str(uuid.uuid4()),
        original_name="test_gobook.jpg",
        stored_name="test_gobook.jpg",
        url_path="/files/test_gobook.jpg",
        local_path="/tmp/test_gobook.jpg",
        file_size=1024,
        file_ext="jpg",
        mime_type="image/jpeg",
        upload_type="FORM",
        created_at=now,
        created_by=user_id,
        updated_at=now,
        updated_by=user_id,
    )
    db.add(file)
    await db.flush()

    file_map = FileMap(
        id=await next_id("FMAP_", db),
        file_id=file.id,
        target_type="POST",
        target_id=post_id,
        file_group="attachment",
        sort_order=0,
        created_at=now,
        created_by=user_id,
        updated_at=now,
        updated_by=user_id,
    )
    db.add(file_map)
    await db.commit()
    await db.refresh(file)
    return file


async def _get_pipeline_run(db: AsyncSession, post_id: str) -> PipelineRun | None:
    result = await db.execute(
        select(PipelineRun).where(
            PipelineRun.post_id == post_id, PipelineRun.trigger_type == "AUTO_REPLY"
        )
    )
    return result.scalar_one_or_none()


async def _get_ai_comment(db: AsyncSession, post_id: str) -> Comment | None:
    result = await db.execute(
        select(Comment).where(
            Comment.post_id == post_id,
            Comment.user_id == settings.ai_agent_user_id,
        )
    )
    return result.scalar_one_or_none()


# ---------------------------------------------------------------------------
# 정상 케이스
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_process_post_completed(db: AsyncSession, monkeypatch):
    """PENDING + delay 경과 + comment_count=0 → COMPLETED, 댓글 생성, PipelineRun 기록"""
    board = await _create_board(db, auto_reply_delay_min=0)
    user = await _create_user(db)
    past = datetime.now(UTC) - timedelta(minutes=10)
    post = await _create_post(db, board.id, user.id, created_at=past)
    now = datetime.now(UTC)

    async def _mock_reply(title: str, content: str) -> str:
        return "해독이의 답변입니다."

    monkeypatch.setattr("app.board.auto_reply_pipeline._generate_reply", _mock_reply)

    await _process_post(db, post, now)

    result = await db.execute(select(Post).where(Post.id == post.id))
    updated = result.scalar_one()
    assert updated.auto_reply_status == "COMPLETED"
    assert updated.auto_reply_at is not None

    comment = await _get_ai_comment(db, post.id)
    assert comment is not None
    assert comment.content == "해독이의 답변입니다."
    assert comment.user_id == settings.ai_agent_user_id

    run = await _get_pipeline_run(db, post.id)
    assert run is not None
    assert run.status == "COMPLETED"
    assert run.success_cnt == 1
    assert run.trigger_type == "AUTO_REPLY"


@pytest.mark.asyncio
async def test_find_eligible_posts_excludes_delay_not_elapsed(db: AsyncSession):
    """delay 미경과 게시글은 _find_eligible_posts 조회에서 제외"""
    board = await _create_board(db, auto_reply_delay_min=60)
    user = await _create_user(db)
    post = await _create_post(db, board.id, user.id)
    now = datetime.now(UTC)

    posts = await _find_eligible_posts(db, now)
    ids = [p.id for p in posts]
    assert post.id not in ids


# ---------------------------------------------------------------------------
# SKIPPED 케이스
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_process_post_skipped_another_worker_preempted(db: AsyncSession, monkeypatch):
    """다른 워커가 RUNNING으로 선점한 경우 → 아무것도 안 함 (status 유지)"""
    board = await _create_board(db)
    user = await _create_user(db)
    post = await _create_post(db, board.id, user.id, auto_reply_status="RUNNING")
    now = datetime.now(UTC)

    async def _mock_reply(title: str, content: str) -> str:
        return "답변"

    monkeypatch.setattr("app.board.auto_reply_pipeline._generate_reply", _mock_reply)

    await _process_post(db, post, now)

    result = await db.execute(select(Post).where(Post.id == post.id))
    updated = result.scalar_one()
    assert updated.auto_reply_status == "RUNNING"

    run = await _get_pipeline_run(db, post.id)
    assert run is None


@pytest.mark.asyncio
async def test_process_post_skipped_when_deleted(db: AsyncSession):
    """delay 중 게시글 삭제(del_yn=True) → SKIPPED, PipelineRun 미생성"""
    board = await _create_board(db)
    user = await _create_user(db)
    post = await _create_post(db, board.id, user.id, del_yn=True)
    now = datetime.now(UTC)

    await _process_post(db, post, now)

    result = await db.execute(select(Post).where(Post.id == post.id))
    updated = result.scalar_one()
    assert updated.auto_reply_status == "SKIPPED"

    run = await _get_pipeline_run(db, post.id)
    assert run is None


@pytest.mark.asyncio
async def test_process_post_skipped_when_comment_exists(db: AsyncSession):
    """delay 중 댓글 생성(comment_count>0) → SKIPPED, PipelineRun 미생성"""
    board = await _create_board(db)
    user = await _create_user(db)
    post = await _create_post(db, board.id, user.id, comment_count=1)
    now = datetime.now(UTC)

    await _process_post(db, post, now)

    result = await db.execute(select(Post).where(Post.id == post.id))
    updated = result.scalar_one()
    assert updated.auto_reply_status == "SKIPPED"

    run = await _get_pipeline_run(db, post.id)
    assert run is None


@pytest.mark.asyncio
async def test_process_post_skipped_when_board_comment_yn_false(db: AsyncSession):
    """delay 중 board.comment_yn=false → SKIPPED, PipelineRun 미생성"""
    board = await _create_board(db, comment_yn=False)
    user = await _create_user(db)
    post = await _create_post(db, board.id, user.id)
    now = datetime.now(UTC)

    await _process_post(db, post, now)

    result = await db.execute(select(Post).where(Post.id == post.id))
    updated = result.scalar_one()
    assert updated.auto_reply_status == "SKIPPED"

    run = await _get_pipeline_run(db, post.id)
    assert run is None


# ---------------------------------------------------------------------------
# AI 실패 케이스
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_process_post_fallback_to_claude(db: AsyncSession, monkeypatch):
    """Gemini 실패 → Claude fallback 성공 → COMPLETED"""
    board = await _create_board(db)
    user = await _create_user(db)
    past = datetime.now(UTC) - timedelta(minutes=10)
    post = await _create_post(db, board.id, user.id, created_at=past)
    now = datetime.now(UTC)

    call_count = {"n": 0}

    async def _mock_reply_fallback(title: str, content: str) -> str:
        call_count["n"] += 1
        return "Claude fallback 답변입니다."

    monkeypatch.setattr("app.board.auto_reply_pipeline._generate_reply", _mock_reply_fallback)

    await _process_post(db, post, now)

    result = await db.execute(select(Post).where(Post.id == post.id))
    updated = result.scalar_one()
    assert updated.auto_reply_status == "COMPLETED"

    comment = await _get_ai_comment(db, post.id)
    assert comment is not None
    assert comment.content == "Claude fallback 답변입니다."


@pytest.mark.asyncio
async def test_process_post_failed_both_ai(db: AsyncSession, monkeypatch):
    """Gemini + Claude 모두 실패 → FAILED, PipelineRun error_msg 기록"""
    board = await _create_board(db)
    user = await _create_user(db)
    past = datetime.now(UTC) - timedelta(minutes=10)
    post = await _create_post(db, board.id, user.id, created_at=past)
    now = datetime.now(UTC)

    async def _mock_reply_fail(title: str, content: str) -> str:
        raise RuntimeError("Gemini: 연결 오류 | Claude: API 키 없음")

    monkeypatch.setattr("app.board.auto_reply_pipeline._generate_reply", _mock_reply_fail)

    await _process_post(db, post, now)

    result = await db.execute(select(Post).where(Post.id == post.id))
    updated = result.scalar_one()
    assert updated.auto_reply_status == "FAILED"

    run = await _get_pipeline_run(db, post.id)
    assert run is not None
    assert run.status == "FAILED"
    assert run.fail_cnt == 1
    assert run.error_msg is not None
    assert "Gemini" in run.error_msg or "Claude" in run.error_msg

    comment = await _get_ai_comment(db, post.id)
    assert comment is None


@pytest.mark.asyncio
async def test_process_post_failed_when_pipeline_run_refresh_fails(db: AsyncSession, monkeypatch):
    """RUNNING 선점 후 PipelineRun 초기화 실패 → Post와 PipelineRun 모두 FAILED"""
    board = await _create_board(db)
    user = await _create_user(db)
    past = datetime.now(UTC) - timedelta(minutes=10)
    post = await _create_post(db, board.id, user.id, created_at=past)
    now = datetime.now(UTC)

    original_refresh = db.refresh

    async def _refresh_fail_on_pipeline_run(instance, *args, **kwargs):
        if isinstance(instance, PipelineRun):
            raise RuntimeError("PipelineRun refresh 실패")
        return await original_refresh(instance, *args, **kwargs)

    async def _mock_reply(title: str, content: str) -> str:
        return "호출되면 안 되는 답변입니다."

    monkeypatch.setattr(db, "refresh", _refresh_fail_on_pipeline_run)
    monkeypatch.setattr("app.board.auto_reply_pipeline._generate_reply", _mock_reply)

    await _process_post(db, post, now)

    result = await db.execute(select(Post).where(Post.id == post.id))
    updated = result.scalar_one()
    assert updated.auto_reply_status == "FAILED"

    run = await _get_pipeline_run(db, post.id)
    assert run is not None
    assert run.status == "FAILED"
    assert run.error_msg is not None
    assert "PipelineRun refresh 실패" in run.error_msg

    comment = await _get_ai_comment(db, post.id)
    assert comment is None


# ---------------------------------------------------------------------------
# SFR-205: 파이프라인 분기 케이스
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_pipeline_board_with_book_id_skipped(db: AsyncSession):
    """pipeline_enabled=true + book_id 있음 → 번역이력 첨부 게시글, SKIPPED"""
    board = await _create_board(db, pipeline_enabled=True)
    user = await _create_user(db)
    book = await _create_book(db, user.id)
    post = await _create_post(db, board.id, user.id, book_id=book.id)
    now = datetime.now(UTC)

    await _process_post(db, post, now)

    result = await db.execute(select(Post).where(Post.id == post.id))
    updated = result.scalar_one()
    assert updated.auto_reply_status == "SKIPPED"

    run = await _get_pipeline_run(db, post.id)
    assert run is None

    comment = await _get_ai_comment(db, post.id)
    assert comment is None


@pytest.mark.asyncio
async def test_pipeline_board_no_image_skipped(db: AsyncSession):
    """pipeline_enabled=true + 이미지 첨부 없음 → OCR 불가, SKIPPED"""
    board = await _create_board(db, pipeline_enabled=True)
    user = await _create_user(db)
    post = await _create_post(db, board.id, user.id)
    now = datetime.now(UTC)

    await _process_post(db, post, now)

    result = await db.execute(select(Post).where(Post.id == post.id))
    updated = result.scalar_one()
    assert updated.auto_reply_status == "SKIPPED"

    run = await _get_pipeline_run(db, post.id)
    assert run is None

    comment = await _get_ai_comment(db, post.id)
    assert comment is None


@pytest.mark.asyncio
async def test_pipeline_board_success(db: AsyncSession, monkeypatch):
    """pipeline_enabled=true + 이미지 있음 → OCR+번역 실행, 댓글 등록, COMPLETED"""
    board = await _create_board(db, pipeline_enabled=True)
    user = await _create_user(db)
    past = datetime.now(UTC) - timedelta(minutes=10)
    post = await _create_post(db, board.id, user.id, created_at=past)
    await _create_image_attachment(db, post.id, user.id)
    now = datetime.now(UTC)

    async def _mock_ocr(local_path: str) -> str:
        return "古書原文텍스트"

    async def _mock_translate(ocr_text: str) -> tuple[str, str]:
        return ("직역 결과입니다.", "의역 결과입니다.")

    monkeypatch.setattr("app.board.auto_reply_pipeline.run_ocr", _mock_ocr)
    monkeypatch.setattr("app.board.auto_reply_pipeline.run_translate", _mock_translate)

    await _process_post(db, post, now)

    result = await db.execute(select(Post).where(Post.id == post.id))
    updated = result.scalar_one()
    assert updated.auto_reply_status == "COMPLETED"
    assert updated.auto_reply_at is not None

    comment = await _get_ai_comment(db, post.id)
    assert comment is not None
    assert "직역:" in comment.content
    assert "의역:" in comment.content
    assert "직역 결과입니다." in comment.content
    assert "의역 결과입니다." in comment.content

    run = await _get_pipeline_run(db, post.id)
    assert run is not None
    assert run.status == "COMPLETED"
    assert run.success_cnt == 1
    assert run.trigger_type == "AUTO_REPLY"


@pytest.mark.asyncio
async def test_pipeline_board_ocr_empty_text_failed(db: AsyncSession, monkeypatch):
    """pipeline_enabled=true + 이미지 있음 + OCR 빈 텍스트 반환 → FAILED, PipelineRun 기록"""
    board = await _create_board(db, pipeline_enabled=True)
    user = await _create_user(db)
    past = datetime.now(UTC) - timedelta(minutes=10)
    post = await _create_post(db, board.id, user.id, created_at=past)
    await _create_image_attachment(db, post.id, user.id)
    now = datetime.now(UTC)

    async def _mock_ocr_empty(local_path: str) -> str:
        return "   "  # 공백만 반환 → strip() 후 빈 문자열

    monkeypatch.setattr("app.board.auto_reply_pipeline.run_ocr", _mock_ocr_empty)

    await _process_post(db, post, now)

    result = await db.execute(select(Post).where(Post.id == post.id))
    updated = result.scalar_one()
    assert updated.auto_reply_status == "FAILED"

    run = await _get_pipeline_run(db, post.id)
    assert run is not None
    assert run.status == "FAILED"
    assert run.fail_cnt == 1
    assert run.error_msg is not None
    assert "OCR" in run.error_msg

    comment = await _get_ai_comment(db, post.id)
    assert comment is None


@pytest.mark.asyncio
async def test_pipeline_board_ocr_exception_failed(db: AsyncSession, monkeypatch):
    """pipeline_enabled=true + 이미지 있음 + run_ocr 예외 → FAILED, PipelineRun error_msg 기록"""
    board = await _create_board(db, pipeline_enabled=True)
    user = await _create_user(db)
    past = datetime.now(UTC) - timedelta(minutes=10)
    post = await _create_post(db, board.id, user.id, created_at=past)
    await _create_image_attachment(db, post.id, user.id)
    now = datetime.now(UTC)

    async def _mock_ocr_fail(local_path: str) -> str:
        raise RuntimeError("Vision API 연결 오류")

    monkeypatch.setattr("app.board.auto_reply_pipeline.run_ocr", _mock_ocr_fail)

    await _process_post(db, post, now)

    result = await db.execute(select(Post).where(Post.id == post.id))
    updated = result.scalar_one()
    assert updated.auto_reply_status == "FAILED"

    run = await _get_pipeline_run(db, post.id)
    assert run is not None
    assert run.status == "FAILED"
    assert run.fail_cnt == 1
    assert run.error_msg is not None
    assert "Vision API" in run.error_msg

    comment = await _get_ai_comment(db, post.id)
    assert comment is None
