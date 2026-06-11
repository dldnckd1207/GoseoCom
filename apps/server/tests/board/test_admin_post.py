"""관리자 게시글 관리 API 테스트"""

import uuid
from datetime import UTC, datetime

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.board.models import Board, Comment, Post, PostHistory
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
    await db.refresh(user)
    return user


async def _create_board(db: AsyncSession) -> Board:
    now = datetime.now(UTC)
    user = await _create_user(db, level=70)
    board = Board(
        id=await next_id("BRD_", db),
        board_code=f"admin_post_{uuid.uuid4().hex[:8]}",
        board_name="관리자 게시글 테스트",
        board_type="LIST",
        read_yn=True,
        guest_read_yn=True,
        write_yn=True,
        guest_write_yn=False,
        notice_yn=True,
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
    await db.commit()
    await db.refresh(board)
    return board


async def _create_post(
    db: AsyncSession,
    board: Board,
    user: User,
    *,
    title: str,
    content: str = "본문",
    notice_yn: bool = False,
    del_yn: bool = False,
) -> Post:
    now = datetime.now(UTC)
    post = Post(
        id=await next_id("POST_", db),
        board_id=board.id,
        user_id=user.id,
        author_name=user.name,
        title=title,
        content=content,
        notice_yn=notice_yn,
        view_count=7,
        comment_count=1,
        auto_reply_status="SKIPPED",
        del_yn=del_yn,
        deleted_at=now if del_yn else None,
        deleted_by=user.id if del_yn else None,
        created_at=now,
        created_by=user.id,
        updated_at=now,
        updated_by=user.id,
    )
    db.add(post)
    await db.commit()
    await db.refresh(post)
    return post


def _token(user: User) -> str:
    return create_access_token(user.id, user_level=user.user_level, user_name=user.name)


@pytest.mark.asyncio
async def test_admin_list_posts_filters_deleted_status(
    auth_client: AsyncClient, db: AsyncSession
) -> None:
    admin = await _create_user(db, level=70)
    user = await _create_user(db, level=10)
    board = await _create_board(db)
    active = await _create_post(db, board, user, title="관리자목록_정상")
    deleted = await _create_post(db, board, user, title="관리자목록_삭제", del_yn=True)

    auth_client.cookies.set("access_token", _token(admin))
    active_resp = await auth_client.post(
        "/admin/api/v1/posts/list",
        json={"keyword": "관리자목록", "deleted_status": "active", "page": 1, "size": 20},
    )
    assert active_resp.status_code == 200
    active_ids = [item["id"] for item in active_resp.json()["body"]["data"]["items"]]
    assert active.id in active_ids
    assert deleted.id not in active_ids

    deleted_resp = await auth_client.post(
        "/admin/api/v1/posts/list",
        json={"keyword": "관리자목록", "deleted_status": "deleted", "page": 1, "size": 20},
    )
    assert deleted_resp.status_code == 200
    deleted_ids = [item["id"] for item in deleted_resp.json()["body"]["data"]["items"]]
    assert deleted.id in deleted_ids
    assert active.id not in deleted_ids

    all_resp = await auth_client.post(
        "/admin/api/v1/posts/list",
        json={"keyword": "관리자목록", "deleted_status": "all", "page": 1, "size": 20},
    )
    assert all_resp.status_code == 200
    all_ids = [item["id"] for item in all_resp.json()["body"]["data"]["items"]]
    assert active.id in all_ids
    assert deleted.id in all_ids


@pytest.mark.asyncio
async def test_admin_list_posts_filters_board_author_notice_keyword(
    auth_client: AsyncClient, db: AsyncSession
) -> None:
    admin = await _create_user(db, level=70)
    user = await _create_user(db, level=10)
    board = await _create_board(db)
    post = await _create_post(
        db,
        board,
        user,
        title="관리자검색_제목",
        content="본문에 고유키워드 포함",
        notice_yn=True,
    )

    auth_client.cookies.set("access_token", _token(admin))
    resp = await auth_client.post(
        "/admin/api/v1/posts/list",
        json={
            "keyword": "고유키워드",
            "board_id": board.id,
            "author_keyword": user.id[-6:],
            "notice_yn": True,
            "deleted_status": "all",
            "page": 1,
            "size": 20,
        },
    )

    assert resp.status_code == 200
    ids = [item["id"] for item in resp.json()["body"]["data"]["items"]]
    assert post.id in ids


@pytest.mark.asyncio
async def test_admin_get_post_does_not_increment_view_count(
    auth_client: AsyncClient, db: AsyncSession
) -> None:
    admin = await _create_user(db, level=70)
    user = await _create_user(db, level=10)
    board = await _create_board(db)
    post = await _create_post(db, board, user, title="조회수 미증가")

    auth_client.cookies.set("access_token", _token(admin))
    resp = await auth_client.get(f"/admin/api/v1/posts/{post.id}")
    assert resp.status_code == 200
    assert resp.json()["body"]["data"]["view_count"] == 7

    await db.refresh(post)
    assert post.view_count == 7


@pytest.mark.asyncio
async def test_admin_get_deleted_post(auth_client: AsyncClient, db: AsyncSession) -> None:
    """관리자 상세 조회는 삭제된 게시글도 조회한다."""
    admin = await _create_user(db, level=70)
    user = await _create_user(db, level=10)
    board = await _create_board(db)
    post = await _create_post(db, board, user, title="삭제 상세", del_yn=True)

    auth_client.cookies.set("access_token", _token(admin))
    resp = await auth_client.get(f"/admin/api/v1/posts/{post.id}")

    assert resp.status_code == 200
    data = resp.json()["body"]["data"]
    assert data["id"] == post.id
    assert data["del_yn"] is True
    assert data["deleted_by_name"] == user.name


@pytest.mark.asyncio
async def test_admin_delete_and_restore_post(auth_client: AsyncClient, db: AsyncSession) -> None:
    admin = await _create_user(db, level=70)
    user = await _create_user(db, level=10)
    board = await _create_board(db)
    post = await _create_post(db, board, user, title="삭제복구")
    comment = Comment(
        id=await next_id("CMT_", db),
        post_id=post.id,
        user_id=user.id,
        author_name=user.name,
        content="댓글",
        created_at=datetime.now(UTC),
        created_by=user.id,
        updated_at=datetime.now(UTC),
        updated_by=user.id,
    )
    db.add(comment)
    await db.commit()

    auth_client.cookies.set("access_token", _token(admin))
    delete_resp = await auth_client.delete(f"/admin/api/v1/posts/{post.id}")
    assert delete_resp.status_code == 200
    await db.refresh(post)
    await db.refresh(comment)
    assert post.del_yn is True
    assert post.deleted_by == admin.id
    assert comment.del_yn is False

    restore_resp = await auth_client.put(f"/admin/api/v1/posts/{post.id}/restore")
    assert restore_resp.status_code == 200
    await db.refresh(post)
    assert post.del_yn is False
    assert post.deleted_at is None
    assert post.deleted_by is None

    history_result = await db.execute(
        select(PostHistory.action)
        .where(PostHistory.post_id == post.id)
        .order_by(PostHistory.version.asc())
    )
    assert history_result.scalars().all() == ["DELETE", "RESTORE"]


@pytest.mark.asyncio
async def test_admin_delete_already_deleted_post(
    auth_client: AsyncClient, db: AsyncSession
) -> None:
    """삭제된 게시글 재삭제 → 400 POST_ALREADY_DELETED"""
    admin = await _create_user(db, level=70)
    user = await _create_user(db, level=10)
    board = await _create_board(db)
    post = await _create_post(db, board, user, title="이미 삭제", del_yn=True)

    auth_client.cookies.set("access_token", _token(admin))
    resp = await auth_client.delete(f"/admin/api/v1/posts/{post.id}")

    assert resp.status_code == 400
    assert resp.json()["header"]["code"] == "POST_ALREADY_DELETED"


@pytest.mark.asyncio
async def test_admin_restore_active_post(auth_client: AsyncClient, db: AsyncSession) -> None:
    """정상 게시글 복구 요청 → 400 POST_NOT_DELETED"""
    admin = await _create_user(db, level=70)
    user = await _create_user(db, level=10)
    board = await _create_board(db)
    post = await _create_post(db, board, user, title="정상 게시글")

    auth_client.cookies.set("access_token", _token(admin))
    resp = await auth_client.put(f"/admin/api/v1/posts/{post.id}/restore")

    assert resp.status_code == 400
    assert resp.json()["header"]["code"] == "POST_NOT_DELETED"


@pytest.mark.asyncio
async def test_admin_posts_forbidden_for_user(auth_client: AsyncClient, db: AsyncSession) -> None:
    user = await _create_user(db, level=10)

    auth_client.cookies.set("access_token", _token(user))
    resp = await auth_client.post("/admin/api/v1/posts/list", json={"page": 1, "size": 20})

    assert resp.status_code == 403
