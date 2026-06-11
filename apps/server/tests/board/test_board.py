"""SFR-105: 게시판 관리 테스트"""

from datetime import UTC, datetime
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.board.models import Board, BoardCategory, Comment, Post
from app.core.common.id_generator import next_id
from app.core.security import create_access_token
from app.core.user.models import User
from tests.conftest import unique_email

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


async def _create_user(db: AsyncSession, user_level: int = 70) -> User:
    user_id = await next_id("USR_", db)
    now = datetime.now(UTC)
    user = User(
        id=user_id,
        email=unique_email(),
        name="테스트유저",
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


async def _create_board(
    auth_client: AsyncClient, token: str, board_code: str, sort_order: int = 99
) -> dict[str, Any]:
    auth_client.cookies.set("access_token", token)
    resp = await auth_client.post(
        "/admin/api/v1/boards",
        json={
            "board_code": board_code,
            "board_name": f"테스트-{board_code}",
            "board_type": "LIST",
            "sort_order": sort_order,
        },
    )
    assert resp.status_code == 201
    data: dict[str, Any] = resp.json()["body"]["data"]
    return data


async def _create_post(
    auth_client: AsyncClient,
    token: str,
    board_code: str,
    title: str = "게시글",
) -> dict[str, Any]:
    auth_client.cookies.set("access_token", token)
    resp = await auth_client.post(
        "/api/v1/posts",
        json={"board_code": board_code, "title": title, "content": "본문"},
    )
    assert resp.status_code == 201
    data: dict[str, Any] = resp.json()["body"]["data"]
    return data


async def _create_comment(auth_client: AsyncClient, token: str, post_id: str) -> dict[str, Any]:
    auth_client.cookies.set("access_token", token)
    resp = await auth_client.post(
        f"/api/v1/posts/{post_id}/comments",
        json={"content": "댓글"},
    )
    assert resp.status_code == 201
    data: dict[str, Any] = resp.json()["body"]["data"]
    return data


# ---------------------------------------------------------------------------
# 정상 케이스
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_guest_list_boards(auth_client: AsyncClient) -> None:
    """GUEST 게시판 목록 조회 → 200, seed 3개 이상"""
    resp = await auth_client.post("/api/v1/boards/list", json={"page": 1, "size": 20})
    assert resp.status_code == 200
    body = resp.json()
    assert body["header"]["success"] is True
    assert body["body"]["data"]["total"] >= 3


@pytest.mark.asyncio
async def test_guest_get_board_by_code(auth_client: AsyncClient) -> None:
    """GUEST 게시판 단건 조회 → 200, 전체 설정 반환"""
    resp = await auth_client.get("/api/v1/boards/translation")
    assert resp.status_code == 200
    data = resp.json()["body"]["data"]
    assert data["board_code"] == "translation"
    assert "read_yn" in data
    assert "guest_read_yn" in data
    assert "attach_size" in data


@pytest.mark.asyncio
async def test_admin_create_board(auth_client: AsyncClient, db: AsyncSession) -> None:
    """ADMIN 게시판 생성 → 201, BRD_ ID 발급"""
    admin = await _create_user(db, user_level=70)
    token = create_access_token(admin.id, user_level=70)
    auth_client.cookies.set("access_token", token)

    resp = await auth_client.post(
        "/admin/api/v1/boards",
        json={
            "board_code": f"test-create-{admin.id[-4:]}",
            "board_name": "생성 테스트",
            "board_type": "LIST",
        },
    )
    assert resp.status_code == 201
    data = resp.json()["body"]["data"]
    assert data["id"].startswith("BRD_")
    assert data["del_yn"] is False


@pytest.mark.asyncio
async def test_admin_update_board(auth_client: AsyncClient, db: AsyncSession) -> None:
    """ADMIN 게시판 수정 → 200, 변경 필드만 반영, board_code 유지"""
    admin = await _create_user(db, user_level=70)
    token = create_access_token(admin.id, user_level=70)
    board = await _create_board(auth_client, token, f"test-upd-{admin.id[-4:]}")

    auth_client.cookies.set("access_token", token)
    resp = await auth_client.put(
        f"/admin/api/v1/boards/{board['id']}",
        json={"board_name": "수정된 이름", "comment_yn": True, "category_yn": True},
    )
    assert resp.status_code == 200
    data = resp.json()["body"]["data"]
    assert data["board_name"] == "수정된 이름"
    assert data["comment_yn"] is True
    assert data["category_yn"] is True
    assert data["board_code"] == board["board_code"]


@pytest.mark.asyncio
async def test_admin_manage_board_categories(auth_client: AsyncClient, db: AsyncSession) -> None:
    """ADMIN 카테고리 생성/목록/수정/삭제 → 정상 처리"""
    admin = await _create_user(db, user_level=70)
    token = create_access_token(admin.id, user_level=70)
    board = await _create_board(auth_client, token, f"test-cat-{admin.id[-4:]}")
    auth_client.cookies.set("access_token", token)

    create_resp = await auth_client.post(
        f"/admin/api/v1/boards/{board['id']}/categories",
        json={"category_name": "조선", "sort_order": 2, "use_yn": True},
    )
    assert create_resp.status_code == 201
    category = create_resp.json()["body"]["data"]
    assert category["id"].startswith("BCAT_")
    assert category["board_id"] == board["id"]
    assert category["category_name"] == "조선"

    list_resp = await auth_client.get(f"/admin/api/v1/boards/{board['id']}/categories")
    assert list_resp.status_code == 200
    items = list_resp.json()["body"]["data"]
    assert [item["id"] for item in items] == [category["id"]]

    update_resp = await auth_client.put(
        f"/admin/api/v1/boards/{board['id']}/categories/{category['id']}",
        json={"category_name": "고려", "sort_order": 1, "use_yn": False},
    )
    assert update_resp.status_code == 200
    updated = update_resp.json()["body"]["data"]
    assert updated["category_name"] == "고려"
    assert updated["sort_order"] == 1
    assert updated["use_yn"] is False

    delete_resp = await auth_client.delete(
        f"/admin/api/v1/boards/{board['id']}/categories/{category['id']}"
    )
    assert delete_resp.status_code == 200
    assert delete_resp.json()["header"]["code"] == "DELETED"

    category_entity = await db.scalar(
        select(BoardCategory).where(BoardCategory.id == category["id"])
    )
    assert category_entity is not None
    assert category_entity.del_yn is True

    list_after_delete = await auth_client.get(f"/admin/api/v1/boards/{board['id']}/categories")
    assert list_after_delete.status_code == 200
    assert list_after_delete.json()["body"]["data"] == []


@pytest.mark.asyncio
async def test_admin_category_requires_matching_board(
    auth_client: AsyncClient, db: AsyncSession
) -> None:
    """다른 게시판의 카테고리 수정/삭제 → 404 CATEGORY_NOT_FOUND"""
    admin = await _create_user(db, user_level=70)
    token = create_access_token(admin.id, user_level=70)
    first_board = await _create_board(auth_client, token, f"test-cat-own-{admin.id[-4:]}")
    second_board = await _create_board(auth_client, token, f"test-cat-other-{admin.id[-4:]}")
    auth_client.cookies.set("access_token", token)
    create_resp = await auth_client.post(
        f"/admin/api/v1/boards/{first_board['id']}/categories",
        json={"category_name": "선사", "sort_order": 0},
    )
    assert create_resp.status_code == 201
    category = create_resp.json()["body"]["data"]

    update_resp = await auth_client.put(
        f"/admin/api/v1/boards/{second_board['id']}/categories/{category['id']}",
        json={"category_name": "삼국"},
    )
    assert update_resp.status_code == 404
    assert update_resp.json()["header"]["code"] == "CATEGORY_NOT_FOUND"

    delete_resp = await auth_client.delete(
        f"/admin/api/v1/boards/{second_board['id']}/categories/{category['id']}"
    )
    assert delete_resp.status_code == 404
    assert delete_resp.json()["header"]["code"] == "CATEGORY_NOT_FOUND"


@pytest.mark.asyncio
async def test_admin_delete_board_no_posts(auth_client: AsyncClient, db: AsyncSession) -> None:
    """게시글 없는 게시판 삭제 → 200 DELETED, 목록 미노출"""
    admin = await _create_user(db, user_level=70)
    token = create_access_token(admin.id, user_level=70)
    board = await _create_board(auth_client, token, f"test-del-{admin.id[-4:]}")

    auth_client.cookies.set("access_token", token)
    resp = await auth_client.delete(f"/admin/api/v1/boards/{board['id']}")
    assert resp.status_code == 200
    assert resp.json()["header"]["code"] == "DELETED"

    auth_client.cookies.clear()
    list_resp = await auth_client.post("/api/v1/boards/list", json={"page": 1, "size": 100})
    codes = [i["board_code"] for i in list_resp.json()["body"]["data"]["items"]]
    assert board["board_code"] not in codes


@pytest.mark.asyncio
async def test_admin_delete_board_soft_deletes_posts_and_comments(
    auth_client: AsyncClient, db: AsyncSession
) -> None:
    """게시글 있는 게시판 삭제 → 게시판/게시글/댓글 모두 논리 삭제"""
    admin = await _create_user(db, user_level=70)
    user = await _create_user(db, user_level=10)
    admin_token = create_access_token(admin.id, user_level=70, user_name=admin.name)
    user_token = create_access_token(user.id, user_level=10, user_name=user.name)
    board = await _create_board(auth_client, admin_token, f"test-del-all-{admin.id[-4:]}")
    auth_client.cookies.set("access_token", admin_token)
    update_resp = await auth_client.put(
        f"/admin/api/v1/boards/{board['id']}",
        json={"comment_yn": True},
    )
    assert update_resp.status_code == 200
    post = await _create_post(auth_client, user_token, board["board_code"])
    comment = await _create_comment(auth_client, user_token, post["id"])

    auth_client.cookies.set("access_token", admin_token)
    resp = await auth_client.delete(f"/admin/api/v1/boards/{board['id']}")
    assert resp.status_code == 200
    assert resp.json()["header"]["code"] == "DELETED"

    board_entity = await db.scalar(select(Board).where(Board.id == board["id"]))
    post_entity = await db.scalar(select(Post).where(Post.id == post["id"]))
    comment_entity = await db.scalar(select(Comment).where(Comment.id == comment["id"]))
    assert board_entity is not None
    assert post_entity is not None
    assert comment_entity is not None
    assert board_entity.del_yn is True
    assert post_entity.del_yn is True
    assert comment_entity.del_yn is True


@pytest.mark.asyncio
async def test_admin_list_boards_includes_all(auth_client: AsyncClient, db: AsyncSession) -> None:
    """ADMIN 목록 조회 → seed 3개 이상 반환"""
    admin = await _create_user(db, user_level=70)
    token = create_access_token(admin.id, user_level=70)
    auth_client.cookies.set("access_token", token)

    resp = await auth_client.post("/admin/api/v1/boards/list", json={"page": 1, "size": 20})
    assert resp.status_code == 200
    assert resp.json()["body"]["data"]["total"] >= 3


@pytest.mark.asyncio
async def test_admin_list_boards_orders_by_id_desc(
    auth_client: AsyncClient, db: AsyncSession
) -> None:
    """ADMIN 목록 조회 → ID 내림차순 정렬"""
    admin = await _create_user(db, user_level=70)
    token = create_access_token(admin.id, user_level=70)
    marker = f"test-order-{admin.id.lower()}"
    first = await _create_board(auth_client, token, f"{marker}-first", sort_order=30)
    second = await _create_board(auth_client, token, f"{marker}-second", sort_order=10)
    third = await _create_board(auth_client, token, f"{marker}-third", sort_order=20)

    auth_client.cookies.set("access_token", token)
    resp = await auth_client.post(
        "/admin/api/v1/boards/list",
        json={"keyword": marker, "page": 1, "size": 20},
    )
    assert resp.status_code == 200
    items = resp.json()["body"]["data"]["items"]
    ids = [item["id"] for item in items]
    assert ids == [third["id"], second["id"], first["id"]]


@pytest.mark.asyncio
async def test_admin_list_boards_uses_id_as_tie_breaker(
    auth_client: AsyncClient, db: AsyncSession
) -> None:
    """ADMIN 목록 조회 → sort_order가 같아도 ID 내림차순 정렬"""
    admin = await _create_user(db, user_level=70)
    token = create_access_token(admin.id, user_level=70)
    marker = f"test-tie-{admin.id.lower()}"
    first = await _create_board(auth_client, token, f"{marker}-z", sort_order=10)
    second = await _create_board(auth_client, token, f"{marker}-a", sort_order=10)

    auth_client.cookies.set("access_token", token)
    resp = await auth_client.post(
        "/admin/api/v1/boards/list",
        json={"keyword": marker, "page": 1, "size": 20},
    )
    assert resp.status_code == 200
    items = resp.json()["body"]["data"]["items"]
    ids = [item["id"] for item in items]
    assert ids == [second["id"], first["id"]]


# ---------------------------------------------------------------------------
# 예외 케이스
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_duplicate_board_code(auth_client: AsyncClient, db: AsyncSession) -> None:
    """중복 board_code 생성 → 409 BOARD_CODE_ALREADY_EXISTS"""
    admin = await _create_user(db, user_level=70)
    token = create_access_token(admin.id, user_level=70)
    code = f"test-dup-{admin.id[-4:]}"
    await _create_board(auth_client, token, code)

    auth_client.cookies.set("access_token", token)
    resp = await auth_client.post(
        "/admin/api/v1/boards",
        json={"board_code": code, "board_name": "중복"},
    )
    assert resp.status_code == 409
    assert resp.json()["header"]["code"] == "BOARD_CODE_ALREADY_EXISTS"


@pytest.mark.asyncio
async def test_update_not_found(auth_client: AsyncClient, db: AsyncSession) -> None:
    """없는 board_id 수정 → 404 BOARD_NOT_FOUND"""
    admin = await _create_user(db, user_level=70)
    token = create_access_token(admin.id, user_level=70)
    auth_client.cookies.set("access_token", token)

    resp = await auth_client.put(
        "/admin/api/v1/boards/BRD_99999999", json={"board_name": "없는게시판"}
    )
    assert resp.status_code == 404
    assert resp.json()["header"]["code"] == "BOARD_NOT_FOUND"


@pytest.mark.asyncio
async def test_delete_not_found(auth_client: AsyncClient, db: AsyncSession) -> None:
    """없는 board_id 삭제 → 404 BOARD_NOT_FOUND"""
    admin = await _create_user(db, user_level=70)
    token = create_access_token(admin.id, user_level=70)
    auth_client.cookies.set("access_token", token)

    resp = await auth_client.delete("/admin/api/v1/boards/BRD_99999999")
    assert resp.status_code == 404
    assert resp.json()["header"]["code"] == "BOARD_NOT_FOUND"


@pytest.mark.asyncio
async def test_unauthenticated_admin_create(auth_client: AsyncClient) -> None:
    """비로그인 ADMIN API 호출 → 401 UNAUTHORIZED"""
    resp = await auth_client.post(
        "/admin/api/v1/boards",
        json={"board_code": "hack", "board_name": "해킹시도"},
    )
    assert resp.status_code == 401
    assert resp.json()["header"]["code"] == "UNAUTHORIZED"


@pytest.mark.asyncio
async def test_user_level_forbidden(auth_client: AsyncClient, db: AsyncSession) -> None:
    """USER 권한으로 ADMIN API 호출 → 403 FORBIDDEN"""
    user = await _create_user(db, user_level=10)
    token = create_access_token(user.id, user_level=10)
    auth_client.cookies.set("access_token", token)

    resp = await auth_client.post(
        "/admin/api/v1/boards",
        json={"board_code": "forbidden", "board_name": "권한없음"},
    )
    assert resp.status_code == 403
    assert resp.json()["header"]["code"] == "FORBIDDEN"


@pytest.mark.asyncio
async def test_get_nonexistent_board_code(auth_client: AsyncClient) -> None:
    """존재하지 않는 board_code 단건 조회 → 404 BOARD_NOT_FOUND"""
    resp = await auth_client.get("/api/v1/boards/nonexistent-board-xyz")
    assert resp.status_code == 404
    assert resp.json()["header"]["code"] == "BOARD_NOT_FOUND"


@pytest.mark.asyncio
async def test_invalid_board_type(auth_client: AsyncClient, db: AsyncSession) -> None:
    """유효하지 않은 board_type → 422"""
    admin = await _create_user(db, user_level=70)
    token = create_access_token(admin.id, user_level=70)
    auth_client.cookies.set("access_token", token)

    resp = await auth_client.post(
        "/admin/api/v1/boards",
        json={"board_code": "invalid-type", "board_name": "타입오류", "board_type": "INVALID"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_board_code_immutable(auth_client: AsyncClient, db: AsyncSession) -> None:
    """board_code는 수정 불가 — 요청에 포함 안 되므로 기존 값 유지"""
    admin = await _create_user(db, user_level=70)
    token = create_access_token(admin.id, user_level=70)
    board = await _create_board(auth_client, token, f"test-immut-{admin.id[-4:]}")
    original_code = board["board_code"]

    auth_client.cookies.set("access_token", token)
    resp = await auth_client.put(
        f"/admin/api/v1/boards/{board['id']}",
        json={"board_name": "이름만 변경"},
    )
    assert resp.status_code == 200
    assert resp.json()["body"]["data"]["board_code"] == original_code
