"""#120: 관리자 댓글 필터링 API 테스트"""

import uuid
from datetime import UTC, datetime

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.board.models import Board, Comment, Post
from app.core.common.id_generator import next_id
from app.core.security import create_access_token
from app.core.user.models import User
from tests.conftest import unique_email


async def _create_user(db: AsyncSession, level: int = 10) -> User:
    now = datetime.now(UTC)
    user_id = await next_id("USR_", db)
    user = User(
        id=user_id,
        email=unique_email(),
        name=f"유저_{user_id[-4:]}",
        user_level=level,
        joined_at=now,
        created_at=now,
        created_by=user_id,
        updated_at=now,
        updated_by=user_id,
    )
    db.add(user)
    await db.commit()
    return user


async def _setup(db: AsyncSession) -> tuple[str, str, str]:
    """board, post, flagged comment 생성 → (board_id, post_id, comment_id)"""
    now = datetime.now(UTC)
    user = await _create_user(db)

    board = Board(
        id=await next_id("BRD_", db),
        board_code=f"admin_filter_{uuid.uuid4().hex[:6]}",
        board_name="관리자 필터 테스트",
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
        created_by=user.id,
        updated_at=now,
        updated_by=user.id,
    )
    db.add(board)
    await db.flush()

    post = Post(
        id=await next_id("POST_", db),
        board_id=board.id,
        user_id=user.id,
        author_name=user.name,
        title="관리자 테스트 게시글",
        content="내용",
        created_at=now,
        created_by=user.id,
        updated_at=now,
        updated_by=user.id,
    )
    db.add(post)
    await db.flush()

    comment = Comment(
        id=await next_id("CMT_", db),
        post_id=post.id,
        user_id=user.id,
        author_name=user.name,
        content="악성 댓글 내용",
        filter_status="FLAGGED",
        is_filtered=True,
        filter_reason="욕설 (confidence: 0.95)",
        filtered_at=now,
        created_at=now,
        created_by=user.id,
        updated_at=now,
        updated_by=user.id,
    )
    db.add(comment)
    await db.commit()
    return board.id, post.id, comment.id


def _admin_token(user_id: str) -> str:
    return create_access_token(user_id, user_level=70)


def _user_token(user_id: str) -> str:
    return create_access_token(user_id, user_level=10)


@pytest.mark.asyncio
async def test_admin_list_flagged_comments(auth_client: AsyncClient, db: AsyncSession):
    """FLAGGED 댓글 목록 조회"""
    admin = await _create_user(db, level=70)
    await _setup(db)

    auth_client.cookies.set("access_token", _admin_token(admin.id))
    resp = await auth_client.post("/admin/api/v1/comments/list", json={"page": 1, "size": 20})

    assert resp.status_code == 200
    data = resp.json()["body"]["data"]
    assert data["total"] >= 1
    assert all(item["filter_reason"] is not None for item in data["items"])


@pytest.mark.asyncio
async def test_admin_approve_comment(auth_client: AsyncClient, db: AsyncSession):
    """승인 — CLEAN 전환 확인"""
    admin = await _create_user(db, level=70)
    _, _, comment_id = await _setup(db)

    auth_client.cookies.set("access_token", _admin_token(admin.id))
    resp = await auth_client.put(f"/admin/api/v1/comments/{comment_id}/approve")

    assert resp.status_code == 200
    data = resp.json()["body"]["data"]
    assert data["filter_reviewed_by"] == admin.id


@pytest.mark.asyncio
async def test_admin_reject_comment(auth_client: AsyncClient, db: AsyncSession):
    """거부 — 소프트 삭제 확인"""
    from sqlalchemy import select as sa_select

    from app.board.models import Comment as CommentModel

    admin = await _create_user(db, level=70)
    _, _, comment_id = await _setup(db)

    auth_client.cookies.set("access_token", _admin_token(admin.id))
    resp = await auth_client.delete(f"/admin/api/v1/comments/{comment_id}")

    assert resp.status_code == 200

    result = await db.execute(sa_select(CommentModel).where(CommentModel.id == comment_id))
    deleted = result.scalar_one()
    assert deleted.del_yn is True


@pytest.mark.asyncio
async def test_admin_list_forbidden_for_user(auth_client: AsyncClient, db: AsyncSession):
    """일반 사용자 접근 → 403"""
    user = await _create_user(db, level=10)

    auth_client.cookies.set("access_token", _user_token(user.id))
    resp = await auth_client.post("/admin/api/v1/comments/list", json={"page": 1, "size": 20})

    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_admin_list_keyword_search(auth_client: AsyncClient, db: AsyncSession):
    """keyword 검색 — 결과가 키워드 포함하는지 확인"""
    admin = await _create_user(db, level=70)
    await _setup(db)

    auth_client.cookies.set("access_token", _admin_token(admin.id))
    resp = await auth_client.post(
        "/admin/api/v1/comments/list",
        json={"keyword": "악성", "page": 1, "size": 20},
    )

    assert resp.status_code == 200
    data = resp.json()["body"]["data"]
    for item in data["items"]:
        assert "악성" in item["content"] or "악성" in item["author_name"]
