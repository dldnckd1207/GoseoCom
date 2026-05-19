"""SFR-105: 게시판 관리 테스트"""

from datetime import UTC, datetime

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

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
) -> dict:
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
    return resp.json()["body"]["data"]


# ---------------------------------------------------------------------------
# 정상 케이스
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_guest_list_boards(auth_client: AsyncClient):
    """GUEST 게시판 목록 조회 → 200, seed 3개 이상"""
    resp = await auth_client.post("/api/v1/boards/list", json={"page": 1, "size": 20})
    assert resp.status_code == 200
    body = resp.json()
    assert body["header"]["success"] is True
    assert body["body"]["data"]["total"] >= 3


@pytest.mark.asyncio
async def test_guest_get_board_by_code(auth_client: AsyncClient):
    """GUEST 게시판 단건 조회 → 200, 전체 설정 반환"""
    resp = await auth_client.get("/api/v1/boards/translation")
    assert resp.status_code == 200
    data = resp.json()["body"]["data"]
    assert data["board_code"] == "translation"
    assert "read_yn" in data
    assert "guest_read_yn" in data
    assert "attach_size" in data


@pytest.mark.asyncio
async def test_admin_create_board(auth_client: AsyncClient, db: AsyncSession):
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
async def test_admin_update_board(auth_client: AsyncClient, db: AsyncSession):
    """ADMIN 게시판 수정 → 200, 변경 필드만 반영, board_code 유지"""
    admin = await _create_user(db, user_level=70)
    token = create_access_token(admin.id, user_level=70)
    board = await _create_board(auth_client, token, f"test-upd-{admin.id[-4:]}")

    auth_client.cookies.set("access_token", token)
    resp = await auth_client.put(
        f"/admin/api/v1/boards/{board['id']}",
        json={"board_name": "수정된 이름", "comment_yn": True},
    )
    assert resp.status_code == 200
    data = resp.json()["body"]["data"]
    assert data["board_name"] == "수정된 이름"
    assert data["comment_yn"] is True
    assert data["board_code"] == board["board_code"]


@pytest.mark.asyncio
async def test_admin_delete_board_no_posts(auth_client: AsyncClient, db: AsyncSession):
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
async def test_admin_list_boards_includes_all(auth_client: AsyncClient, db: AsyncSession):
    """ADMIN 목록 조회 → seed 3개 이상 반환"""
    admin = await _create_user(db, user_level=70)
    token = create_access_token(admin.id, user_level=70)
    auth_client.cookies.set("access_token", token)

    resp = await auth_client.post("/admin/api/v1/boards/list", json={"page": 1, "size": 20})
    assert resp.status_code == 200
    assert resp.json()["body"]["data"]["total"] >= 3


# ---------------------------------------------------------------------------
# 예외 케이스
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_duplicate_board_code(auth_client: AsyncClient, db: AsyncSession):
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
async def test_update_not_found(auth_client: AsyncClient, db: AsyncSession):
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
async def test_delete_not_found(auth_client: AsyncClient, db: AsyncSession):
    """없는 board_id 삭제 → 404 BOARD_NOT_FOUND"""
    admin = await _create_user(db, user_level=70)
    token = create_access_token(admin.id, user_level=70)
    auth_client.cookies.set("access_token", token)

    resp = await auth_client.delete("/admin/api/v1/boards/BRD_99999999")
    assert resp.status_code == 404
    assert resp.json()["header"]["code"] == "BOARD_NOT_FOUND"


@pytest.mark.asyncio
async def test_unauthenticated_admin_create(auth_client: AsyncClient):
    """비로그인 ADMIN API 호출 → 401 UNAUTHORIZED"""
    resp = await auth_client.post(
        "/admin/api/v1/boards",
        json={"board_code": "hack", "board_name": "해킹시도"},
    )
    assert resp.status_code == 401
    assert resp.json()["header"]["code"] == "UNAUTHORIZED"


@pytest.mark.asyncio
async def test_user_level_forbidden(auth_client: AsyncClient, db: AsyncSession):
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
async def test_get_nonexistent_board_code(auth_client: AsyncClient):
    """존재하지 않는 board_code 단건 조회 → 404 BOARD_NOT_FOUND"""
    resp = await auth_client.get("/api/v1/boards/nonexistent-board-xyz")
    assert resp.status_code == 404
    assert resp.json()["header"]["code"] == "BOARD_NOT_FOUND"


@pytest.mark.asyncio
async def test_invalid_board_type(auth_client: AsyncClient, db: AsyncSession):
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
async def test_board_code_immutable(auth_client: AsyncClient, db: AsyncSession):
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
