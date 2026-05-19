"""SFR-101: 댓글 CRUD 테스트"""

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


async def _create_post(auth_client: AsyncClient, token: str) -> dict:
    auth_client.cookies.set("access_token", token)
    resp = await auth_client.post(
        "/api/v1/posts",
        json={"board_code": "questions", "title": "댓글 테스트 게시글", "content": "본문"},
    )
    assert resp.status_code == 201
    return resp.json()["body"]["data"]


async def _create_comment(
    auth_client: AsyncClient, token: str, post_id: str, content: str = "댓글"
) -> dict:
    auth_client.cookies.set("access_token", token)
    resp = await auth_client.post(
        f"/api/v1/posts/{post_id}/comments",
        json={"content": content},
    )
    assert resp.status_code == 201
    return resp.json()["body"]["data"]


# ---------------------------------------------------------------------------
# 정상 케이스
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_comments_nested(auth_client: AsyncClient, db: AsyncSession):
    """댓글 목록 → Nested 구조, root 기준 total"""
    user = await _create_user(db)
    token = create_access_token(user.id, user_level=10, user_name=user.name)
    post = await _create_post(auth_client, token)
    post_id = post["id"]

    root = await _create_comment(auth_client, token, post_id, "root 댓글")

    # 대댓글 작성
    auth_client.cookies.set("access_token", token)
    resp = await auth_client.post(
        f"/api/v1/posts/{post_id}/comments",
        json={"content": "대댓글", "parent_id": root["id"]},
    )
    assert resp.status_code == 201

    auth_client.cookies.clear()
    list_resp = await auth_client.post(
        f"/api/v1/posts/{post_id}/comments/list",
        json={"page": 1, "size": 20},
    )
    assert list_resp.status_code == 200
    data = list_resp.json()["body"]["data"]
    assert data["total"] == 1  # root 1개 기준
    assert len(data["items"][0]["replies"]) == 1
    assert data["items"][0]["replies"][0]["depth"] == 1


@pytest.mark.asyncio
async def test_comment_count_increment(auth_client: AsyncClient, db: AsyncSession):
    """댓글 작성 → post.comment_count +1"""
    user = await _create_user(db)
    token = create_access_token(user.id, user_level=10, user_name=user.name)
    post = await _create_post(auth_client, token)
    post_id = post["id"]

    auth_client.cookies.clear()
    before = (await auth_client.get(f"/api/v1/posts/{post_id}")).json()["body"]["data"][
        "comment_count"
    ]

    await _create_comment(auth_client, token, post_id)

    auth_client.cookies.clear()
    after = (await auth_client.get(f"/api/v1/posts/{post_id}")).json()["body"]["data"][
        "comment_count"
    ]
    assert after == before + 1


@pytest.mark.asyncio
async def test_comment_count_decrement(auth_client: AsyncClient, db: AsyncSession):
    """댓글 삭제 → post.comment_count -1"""
    user = await _create_user(db)
    token = create_access_token(user.id, user_level=10, user_name=user.name)
    post = await _create_post(auth_client, token)
    post_id = post["id"]
    comment = await _create_comment(auth_client, token, post_id)

    auth_client.cookies.set("access_token", token)
    await auth_client.delete(f"/api/v1/posts/{post_id}/comments/{comment['id']}")

    auth_client.cookies.clear()
    count = (await auth_client.get(f"/api/v1/posts/{post_id}")).json()["body"]["data"][
        "comment_count"
    ]
    assert count == 0


@pytest.mark.asyncio
async def test_deleted_comment_placeholder(auth_client: AsyncClient, db: AsyncSession):
    """root 댓글 삭제 후 목록에서 placeholder로 노출"""
    user = await _create_user(db)
    token = create_access_token(user.id, user_level=10, user_name=user.name)
    post = await _create_post(auth_client, token)
    post_id = post["id"]
    comment = await _create_comment(auth_client, token, post_id, "삭제될 댓글")

    auth_client.cookies.set("access_token", token)
    await auth_client.delete(f"/api/v1/posts/{post_id}/comments/{comment['id']}")

    auth_client.cookies.clear()
    list_resp = await auth_client.post(
        f"/api/v1/posts/{post_id}/comments/list",
        json={"page": 1, "size": 20},
    )
    items = list_resp.json()["body"]["data"]["items"]
    assert len(items) == 1
    assert items[0]["is_deleted"] is True
    assert items[0]["author_name"] is None
    assert "삭제된 댓글" in items[0]["content"]


@pytest.mark.asyncio
async def test_update_comment(auth_client: AsyncClient, db: AsyncSession):
    """댓글 수정 → 200 UPDATED"""
    user = await _create_user(db)
    token = create_access_token(user.id, user_level=10, user_name=user.name)
    post = await _create_post(auth_client, token)
    comment = await _create_comment(auth_client, token, post["id"])

    auth_client.cookies.set("access_token", token)
    resp = await auth_client.put(
        f"/api/v1/posts/{post['id']}/comments/{comment['id']}",
        json={"content": "수정된 내용"},
    )
    assert resp.status_code == 200
    assert resp.json()["body"]["data"]["content"] == "수정된 내용"


# ---------------------------------------------------------------------------
# 예외 케이스
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_reply_depth_limit(auth_client: AsyncClient, db: AsyncSession):
    """depth=1 댓글에 대댓글 시도 → 403 REPLY_NOT_ALLOWED"""
    user = await _create_user(db)
    token = create_access_token(user.id, user_level=10, user_name=user.name)
    post = await _create_post(auth_client, token)
    post_id = post["id"]
    root = await _create_comment(auth_client, token, post_id)

    auth_client.cookies.set("access_token", token)
    reply = await auth_client.post(
        f"/api/v1/posts/{post_id}/comments",
        json={"content": "대댓글", "parent_id": root["id"]},
    )
    reply_id = reply.json()["body"]["data"]["id"]

    # 대댓글의 대댓글 시도
    resp = await auth_client.post(
        f"/api/v1/posts/{post_id}/comments",
        json={"content": "대대댓글", "parent_id": reply_id},
    )
    assert resp.status_code == 403
    assert resp.json()["header"]["code"] == "REPLY_NOT_ALLOWED"


@pytest.mark.asyncio
async def test_comment_wrong_post_id(auth_client: AsyncClient, db: AsyncSession):
    """다른 post_id로 댓글 수정 시도 → 404 COMMENT_NOT_FOUND"""
    user = await _create_user(db)
    token = create_access_token(user.id, user_level=10, user_name=user.name)
    post1 = await _create_post(auth_client, token)
    post2 = await _create_post(auth_client, token)
    comment = await _create_comment(auth_client, token, post1["id"])

    auth_client.cookies.set("access_token", token)
    resp = await auth_client.put(
        f"/api/v1/posts/{post2['id']}/comments/{comment['id']}",
        json={"content": "잘못된 접근"},
    )
    assert resp.status_code == 404
    assert resp.json()["header"]["code"] == "COMMENT_NOT_FOUND"


@pytest.mark.asyncio
async def test_delete_comment_forbidden(auth_client: AsyncClient, db: AsyncSession):
    """타인 댓글 삭제 → 403 FORBIDDEN"""
    owner = await _create_user(db)
    other = await _create_user(db)
    owner_token = create_access_token(owner.id, user_level=10, user_name=owner.name)
    other_token = create_access_token(other.id, user_level=10, user_name=other.name)

    post = await _create_post(auth_client, owner_token)
    comment = await _create_comment(auth_client, owner_token, post["id"])

    auth_client.cookies.set("access_token", other_token)
    resp = await auth_client.delete(f"/api/v1/posts/{post['id']}/comments/{comment['id']}")
    assert resp.status_code == 403
    assert resp.json()["header"]["code"] == "FORBIDDEN"
