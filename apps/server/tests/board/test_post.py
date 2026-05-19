"""SFR-101: 게시글 CRUD 테스트"""

from datetime import UTC, datetime

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.board.models import Board
from app.core.common.id_generator import next_id
from app.core.security import create_access_token
from app.core.user.models import User
from tests.conftest import unique_email

# ---------------------------------------------------------------------------
# Fixtures
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


async def _create_post(
    auth_client: AsyncClient,
    token: str,
    board_code: str = "translation",
    title: str = "테스트 제목",
    content: str = "테스트 본문",
) -> dict:
    auth_client.cookies.set("access_token", token)
    resp = await auth_client.post(
        "/api/v1/posts",
        json={"board_code": board_code, "title": title, "content": content},
    )
    assert resp.status_code == 201
    return resp.json()["body"]["data"]


# ---------------------------------------------------------------------------
# 정상 케이스
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_posts_guest(auth_client: AsyncClient):
    """GUEST 게시글 목록 조회 → 200"""
    resp = await auth_client.post(
        "/api/v1/posts/list",
        json={"board_codes": ["translation"], "page": 1, "size": 20},
    )
    assert resp.status_code == 200
    data = resp.json()["body"]["data"]
    assert "items" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_create_post(auth_client: AsyncClient, db: AsyncSession):
    """USER 게시글 작성 → 201, POST_ ID 발급, author_name 스냅샷"""
    user = await _create_user(db)
    token = create_access_token(user.id, user_level=10, user_name=user.name)

    auth_client.cookies.set("access_token", token)
    resp = await auth_client.post(
        "/api/v1/posts",
        json={"board_code": "translation", "title": "제목", "content": "본문"},
    )
    assert resp.status_code == 201
    data = resp.json()["body"]["data"]
    assert data["id"].startswith("POST_")
    assert data["author_name"] == user.name
    assert data["is_ai_gen"] is False
    assert data["board_code"] == "translation"


@pytest.mark.asyncio
async def test_get_post_increments_view_count(auth_client: AsyncClient, db: AsyncSession):
    """게시글 단건 조회 → view_count +1"""
    user = await _create_user(db)
    token = create_access_token(user.id, user_level=10, user_name=user.name)
    post = await _create_post(auth_client, token)
    post_id = post["id"]

    auth_client.cookies.clear()
    resp1 = await auth_client.get(f"/api/v1/posts/{post_id}")
    assert resp1.status_code == 200
    view1 = resp1.json()["body"]["data"]["view_count"]

    resp2 = await auth_client.get(f"/api/v1/posts/{post_id}")
    view2 = resp2.json()["body"]["data"]["view_count"]
    assert view2 == view1 + 1


@pytest.mark.asyncio
async def test_update_post(auth_client: AsyncClient, db: AsyncSession):
    """게시글 수정 → 200 UPDATED, 변경 필드만 반영"""
    user = await _create_user(db)
    token = create_access_token(user.id, user_level=10, user_name=user.name)
    post = await _create_post(auth_client, token, title="원래 제목")

    auth_client.cookies.set("access_token", token)
    resp = await auth_client.put(
        f"/api/v1/posts/{post['id']}",
        json={"title": "수정된 제목"},
    )
    assert resp.status_code == 200
    data = resp.json()["body"]["data"]
    assert data["title"] == "수정된 제목"
    assert data["content"] == post["content"]


@pytest.mark.asyncio
async def test_delete_post(auth_client: AsyncClient, db: AsyncSession):
    """게시글 삭제 → 200 DELETED, 목록 미노출"""
    user = await _create_user(db)
    token = create_access_token(user.id, user_level=10, user_name=user.name)
    post = await _create_post(auth_client, token)

    auth_client.cookies.set("access_token", token)
    resp = await auth_client.delete(f"/api/v1/posts/{post['id']}")
    assert resp.status_code == 200
    assert resp.json()["header"]["code"] == "DELETED"

    auth_client.cookies.clear()
    get_resp = await auth_client.get(f"/api/v1/posts/{post['id']}")
    assert get_resp.status_code == 404


# ---------------------------------------------------------------------------
# 예외 케이스
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_posts_unknown_board_codes(auth_client: AsyncClient):
    """존재하지 않는 board_codes → 200, 빈 목록 반환"""
    resp = await auth_client.post(
        "/api/v1/posts/list",
        json={"board_codes": ["nonexistent"], "page": 1, "size": 20},
    )
    assert resp.status_code == 200
    data = resp.json()["body"]["data"]
    assert data["items"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_get_post_not_found(auth_client: AsyncClient):
    """없는 post_id 단건 조회 → 404 POST_NOT_FOUND"""
    resp = await auth_client.get("/api/v1/posts/POST_99999999")
    assert resp.status_code == 404
    assert resp.json()["header"]["code"] == "POST_NOT_FOUND"


@pytest.mark.asyncio
async def test_create_post_unauthenticated(auth_client: AsyncClient):
    """비로그인 게시글 작성 → 401"""
    resp = await auth_client.post(
        "/api/v1/posts",
        json={"board_code": "translation", "title": "제목", "content": "본문"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_update_post_forbidden(auth_client: AsyncClient, db: AsyncSession):
    """타인의 게시글 수정 → 403 FORBIDDEN"""
    owner = await _create_user(db)
    other = await _create_user(db)
    owner_token = create_access_token(owner.id, user_level=10, user_name=owner.name)
    other_token = create_access_token(other.id, user_level=10, user_name=other.name)

    post = await _create_post(auth_client, owner_token)

    auth_client.cookies.set("access_token", other_token)
    resp = await auth_client.put(
        f"/api/v1/posts/{post['id']}",
        json={"title": "수정 시도"},
    )
    assert resp.status_code == 403
    assert resp.json()["header"]["code"] == "FORBIDDEN"


@pytest.mark.asyncio
async def test_notice_requires_admin(auth_client: AsyncClient, db: AsyncSession):
    """USER가 notice_yn=true 설정 → 403 FORBIDDEN"""
    user = await _create_user(db, user_level=10)
    token = create_access_token(user.id, user_level=10, user_name=user.name)

    auth_client.cookies.set("access_token", token)
    resp = await auth_client.post(
        "/api/v1/posts",
        json={
            "board_code": "translation",
            "title": "공지시도",
            "content": "본문",
            "notice_yn": True,
        },
    )
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# board_group 정책 테스트
# ---------------------------------------------------------------------------


async def _create_board(
    db: AsyncSession,
    board_code: str,
    board_group: str | None = "community",
    guest_read_yn: bool = True,
) -> Board:
    """테스트용 게시판 생성 헬퍼"""
    now = datetime.now(UTC)
    board_id = await next_id("BRD_", db)
    board = Board(
        id=board_id,
        board_code=board_code,
        board_name="테스트게시판",
        board_type="LIST",
        read_yn=True,
        guest_read_yn=guest_read_yn,
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
        auto_reply_delay_min=5,
        pipeline_enabled=False,
        sort_order=99,
        use_yn=True,
        board_group=board_group,
        created_at=now,
        created_by="USR_00000000",
        updated_at=now,
        updated_by="USR_00000000",
    )
    db.add(board)
    await db.commit()
    await db.refresh(board)
    return board


@pytest.mark.asyncio
async def test_community_board_list_accessible_without_login(
    auth_client: AsyncClient, db: AsyncSession
):
    """board_group=community + guest_read_yn=false → 비로그인 목록 조회 200 (게시글 포함)"""
    board = await _create_board(db, board_code="test_restricted_list", guest_read_yn=False)

    user = await _create_user(db)
    token = create_access_token(user.id, user_level=10, user_name=user.name)
    await _create_post(auth_client, token, board_code=board.board_code)

    auth_client.cookies.clear()
    resp = await auth_client.post(
        "/api/v1/posts/list",
        json={"board_codes": [board.board_code], "page": 1, "size": 20},
    )
    assert resp.status_code == 200
    data = resp.json()["body"]["data"]
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_community_board_detail_forbidden_without_login(
    auth_client: AsyncClient, db: AsyncSession
):
    """board_group=community + guest_read_yn=false → 비로그인 상세 조회 403"""
    board = await _create_board(db, board_code="test_restricted_detail", guest_read_yn=False)

    user = await _create_user(db)
    token = create_access_token(user.id, user_level=10, user_name=user.name)
    post_data = await _create_post(auth_client, token, board_code=board.board_code)

    auth_client.cookies.clear()
    resp = await auth_client.get(f"/api/v1/posts/{post_data['id']}")
    assert resp.status_code == 403
