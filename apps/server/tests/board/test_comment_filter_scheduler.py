"""#120: 악성 댓글 필터링 스케줄러 테스트"""

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.board.comment_filter_scheduler import (
    _find_pending_comments,
    _process_comment,
)
from app.board.models import Board, Comment, Post
from app.config import settings
from app.core.common.id_generator import next_id
from app.core.user.models import User
from tests.conftest import unique_email


async def _create_user(db: AsyncSession) -> User:
    now = datetime.now(UTC)
    user_id = await next_id("USR_", db)
    user = User(
        id=user_id,
        email=unique_email(),
        name="테스터",
        user_level=10,
        joined_at=now,
        created_at=now,
        created_by=user_id,
        updated_at=now,
        updated_by=user_id,
    )
    db.add(user)
    await db.commit()
    return user


async def _create_board_and_post(db: AsyncSession, user_id: str) -> Post:
    now = datetime.now(UTC)
    board = Board(
        id=await next_id("BRD_", db),
        board_code=f"filter_test_{uuid.uuid4().hex[:6]}",
        board_name="필터링 테스트",
        board_type="LIST",
        read_yn=True,
        guest_read_yn=True,
        write_yn=True,
        guest_write_yn=False,
        notice_yn=False,
        reply_yn=False,
        comment_yn=True,
        secret_yn=False,
        like_yn=False,
        category_yn=False,
        attach_yn=False,
        attach_size=10240,
        attach_count=5,
        list_count=20,
        auto_reply_enabled=False,
        auto_reply_delay_min=0,
        pipeline_enabled=False,
        sort_order=99,
        use_yn=True,
        created_at=now,
        created_by=user_id,
        updated_at=now,
        updated_by=user_id,
    )
    db.add(board)
    await db.flush()

    post = Post(
        id=await next_id("POST_", db),
        board_id=board.id,
        user_id=user_id,
        author_name="테스터",
        title="테스트 게시글",
        content="내용",
        created_at=now,
        created_by=user_id,
        updated_at=now,
        updated_by=user_id,
    )
    db.add(post)
    await db.commit()
    return post


async def _create_comment(
    db: AsyncSession, post_id: str, user_id: str, filter_status: str = "PENDING"
) -> Comment:
    now = datetime.now(UTC)
    comment = Comment(
        id=await next_id("CMT_", db),
        post_id=post_id,
        user_id=user_id,
        author_name="테스터",
        content="테스트 댓글",
        filter_status=filter_status,
        created_at=now,
        created_by=user_id,
        updated_at=now,
        updated_by=user_id,
    )
    db.add(comment)
    await db.commit()
    return comment


@pytest.mark.asyncio
async def test_find_pending_excludes_ai(db: AsyncSession):
    """AI 생성 댓글은 PENDING 목록에서 제외"""
    user = await _create_user(db)
    post = await _create_board_and_post(db, user.id)

    # 일반 사용자 댓글
    normal = await _create_comment(db, post.id, user.id)
    # AI 댓글
    ai_comment = await _create_comment(db, post.id, settings.ai_agent_user_id)

    result = await _find_pending_comments(db, limit=100)
    ids = [c.id for c in result]
    assert normal.id in ids
    assert ai_comment.id not in ids


@pytest.mark.asyncio
async def test_process_comment_flagged(db: AsyncSession):
    """악성 판별 시 FLAGGED + is_filtered=True 업데이트"""
    user = await _create_user(db)
    post = await _create_board_and_post(db, user.id)
    comment = await _create_comment(db, post.id, user.id)

    with patch(
        "app.board.comment_filter_scheduler.run_filter",
        new=AsyncMock(return_value=(True, "욕설", 0.95)),
    ):
        await _process_comment(db, comment, datetime.now(UTC))

    result = await db.execute(select(Comment).where(Comment.id == comment.id))
    updated = result.scalar_one()
    assert updated.filter_status == "FLAGGED"
    assert updated.is_filtered is True
    assert updated.filter_reason is not None


@pytest.mark.asyncio
async def test_process_comment_clean(db: AsyncSession):
    """정상 판별 시 CLEAN 업데이트"""
    user = await _create_user(db)
    post = await _create_board_and_post(db, user.id)
    comment = await _create_comment(db, post.id, user.id)

    with patch(
        "app.board.comment_filter_scheduler.run_filter",
        new=AsyncMock(return_value=(False, "", 0.01)),
    ):
        await _process_comment(db, comment, datetime.now(UTC))

    result = await db.execute(select(Comment).where(Comment.id == comment.id))
    updated = result.scalar_one()
    assert updated.filter_status == "CLEAN"
    assert updated.is_filtered is False


@pytest.mark.asyncio
async def test_process_comment_api_error_keeps_pending(db: AsyncSession):
    """Gemini API 오류 시 PENDING 유지"""
    user = await _create_user(db)
    post = await _create_board_and_post(db, user.id)
    comment = await _create_comment(db, post.id, user.id)

    with patch(
        "app.board.comment_filter_scheduler.run_filter", side_effect=RuntimeError("API 오류")
    ):
        await _process_comment(db, comment, datetime.now(UTC))

    result = await db.execute(select(Comment).where(Comment.id == comment.id))
    updated = result.scalar_one()
    assert updated.filter_status == "PENDING"


@pytest.mark.asyncio
async def test_find_pending_respects_limit(db: AsyncSession):
    """배치 사이즈 limit 적용 확인"""
    user = await _create_user(db)
    post = await _create_board_and_post(db, user.id)
    for _ in range(5):
        await _create_comment(db, post.id, user.id)

    result = await _find_pending_comments(db, limit=2)
    assert len(result) <= 2
