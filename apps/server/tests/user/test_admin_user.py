"""관리자 사용자 관리 테스트"""

from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.common.id_generator import next_id
from app.core.security import create_access_token
from app.core.user.models import User, UserToken
from tests.conftest import unique_email


async def _create_user(db: AsyncSession, user_level: int = 10, name: str = "테스트유저") -> User:
    user_id = await next_id("USR_", db)
    now = datetime.now(UTC)
    user = User(
        id=user_id,
        email=unique_email(),
        name=name,
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


async def _create_token(db: AsyncSession, user_id: str) -> UserToken:
    token = UserToken(
        id=await next_id("UTKN_", db),
        user_id=user_id,
        token_hash=f"hash-{user_id}-{datetime.now(UTC).timestamp()}",
        expires_at=datetime.now(UTC) + timedelta(days=30),
        is_revoked=False,
        created_at=datetime.now(UTC),
        created_by=user_id,
    )
    db.add(token)
    await db.commit()
    await db.refresh(token)
    return token


def _set_admin_cookie(auth_client: AsyncClient, user: User) -> None:
    auth_client.cookies.set(
        "access_token",
        create_access_token(user.id, user_level=user.user_level, user_name=user.name),
    )


@pytest.mark.asyncio
async def test_admin_list_users(auth_client: AsyncClient, db: AsyncSession) -> None:
    admin = await _create_user(db, user_level=70)
    user = await _create_user(db, user_level=10, name="홍길동")
    _set_admin_cookie(auth_client, admin)

    resp = await auth_client.post(
        "/admin/api/v1/users/list",
        json={"keyword": "홍길", "role": "user", "page": 1, "size": 10},
    )

    assert resp.status_code == 200
    data = resp.json()["body"]["data"]
    ids = [item["id"] for item in data["items"]]
    assert user.id in ids
    assert data["total"] >= 1
    assert data["items"][0]["role_label"] == "사용자"


@pytest.mark.asyncio
async def test_admin_list_filters_use_and_block(auth_client: AsyncClient, db: AsyncSession) -> None:
    admin = await _create_user(db, user_level=70)
    active = await _create_user(db, user_level=10)
    blocked = await _create_user(db, user_level=10)
    blocked.block_yn = True
    inactive = await _create_user(db, user_level=10)
    inactive.use_yn = False
    await db.commit()
    _set_admin_cookie(auth_client, admin)

    block_resp = await auth_client.post(
        "/admin/api/v1/users/list",
        json={"block_yn": True, "page": 1, "size": 50},
    )
    assert block_resp.status_code == 200
    block_ids = [item["id"] for item in block_resp.json()["body"]["data"]["items"]]
    assert blocked.id in block_ids
    assert active.id not in block_ids

    use_resp = await auth_client.post(
        "/admin/api/v1/users/list",
        json={"use_yn": False, "page": 1, "size": 50},
    )
    use_ids = [item["id"] for item in use_resp.json()["body"]["data"]["items"]]
    assert inactive.id in use_ids


@pytest.mark.asyncio
async def test_admin_update_status(auth_client: AsyncClient, db: AsyncSession) -> None:
    admin = await _create_user(db, user_level=70)
    user = await _create_user(db, user_level=10)
    _set_admin_cookie(auth_client, admin)

    resp = await auth_client.put(
        f"/admin/api/v1/users/{user.id}",
        json={"use_yn": False, "block_yn": True},
    )

    assert resp.status_code == 200
    data = resp.json()["body"]["data"]
    assert data["use_yn"] is False
    assert data["block_yn"] is True
    await db.refresh(user)
    assert user.blocked_by == admin.id
    assert user.blocked_at is not None


@pytest.mark.asyncio
async def test_admin_update_status_allows_unchanged_user_level_payload(
    auth_client: AsyncClient, db: AsyncSession
) -> None:
    """일반 관리자 상태 저장 — 프론트 전체 payload에 변경 없는 user_level이 포함돼도 허용"""
    admin = await _create_user(db, user_level=70)
    user = await _create_user(db, user_level=10)
    _set_admin_cookie(auth_client, admin)

    resp = await auth_client.put(
        f"/admin/api/v1/users/{user.id}",
        json={"user_level": 10, "use_yn": False, "block_yn": False},
    )

    assert resp.status_code == 200
    data = resp.json()["body"]["data"]
    assert data["user_level"] == 10
    assert data["use_yn"] is False


@pytest.mark.asyncio
async def test_admin_update_level_forbidden(auth_client: AsyncClient, db: AsyncSession) -> None:
    admin = await _create_user(db, user_level=70)
    user = await _create_user(db, user_level=10)
    _set_admin_cookie(auth_client, admin)

    resp = await auth_client.put(
        f"/admin/api/v1/users/{user.id}",
        json={"user_level": 70},
    )

    assert resp.status_code == 403
    assert resp.json()["header"]["code"] == "SYSTEM_ADMIN_ONLY"


@pytest.mark.asyncio
async def test_admin_force_withdraw_forbidden(auth_client: AsyncClient, db: AsyncSession) -> None:
    admin = await _create_user(db, user_level=70)
    user = await _create_user(db, user_level=10)
    _set_admin_cookie(auth_client, admin)

    resp = await auth_client.request(
        "DELETE",
        f"/admin/api/v1/users/{user.id}",
        json={"left_reason": "권한 부족"},
    )

    assert resp.status_code == 403
    assert resp.json()["header"]["code"] == "SYSTEM_ADMIN_ONLY"


@pytest.mark.asyncio
async def test_admin_cannot_update_system_admin_status(
    auth_client: AsyncClient, db: AsyncSession
) -> None:
    admin = await _create_user(db, user_level=70)
    system_admin = await _create_user(db, user_level=100)
    _set_admin_cookie(auth_client, admin)

    resp = await auth_client.put(
        f"/admin/api/v1/users/{system_admin.id}",
        json={"block_yn": True},
    )

    assert resp.status_code == 403
    assert resp.json()["header"]["code"] == "SYSTEM_ADMIN_ONLY"


@pytest.mark.asyncio
async def test_system_admin_update_level(auth_client: AsyncClient, db: AsyncSession) -> None:
    system_admin = await _create_user(db, user_level=100)
    user = await _create_user(db, user_level=10)
    _set_admin_cookie(auth_client, system_admin)

    resp = await auth_client.put(
        f"/admin/api/v1/users/{user.id}",
        json={"user_level": 70},
    )

    assert resp.status_code == 200
    assert resp.json()["body"]["data"]["user_level"] == 70


@pytest.mark.asyncio
async def test_self_update_is_rejected(auth_client: AsyncClient, db: AsyncSession) -> None:
    admin = await _create_user(db, user_level=100)
    _set_admin_cookie(auth_client, admin)

    resp = await auth_client.put(
        f"/admin/api/v1/users/{admin.id}",
        json={"block_yn": True},
    )

    assert resp.status_code == 400
    assert resp.json()["header"]["code"] == "SELF_PROTECTION"


@pytest.mark.asyncio
async def test_disable_revokes_refresh_tokens(auth_client: AsyncClient, db: AsyncSession) -> None:
    admin = await _create_user(db, user_level=70)
    user = await _create_user(db, user_level=10)
    token = await _create_token(db, user.id)
    _set_admin_cookie(auth_client, admin)

    resp = await auth_client.put(
        f"/admin/api/v1/users/{user.id}",
        json={"use_yn": False},
    )

    assert resp.status_code == 200
    refreshed = await db.scalar(select(UserToken).where(UserToken.id == token.id))
    assert refreshed is not None
    assert refreshed.is_revoked is True


@pytest.mark.asyncio
async def test_block_revokes_refresh_tokens(auth_client: AsyncClient, db: AsyncSession) -> None:
    admin = await _create_user(db, user_level=70)
    user = await _create_user(db, user_level=10)
    token = await _create_token(db, user.id)
    _set_admin_cookie(auth_client, admin)

    resp = await auth_client.put(
        f"/admin/api/v1/users/{user.id}",
        json={"block_yn": True},
    )

    assert resp.status_code == 200
    refreshed = await db.scalar(select(UserToken).where(UserToken.id == token.id))
    assert refreshed is not None
    assert refreshed.is_revoked is True


@pytest.mark.asyncio
async def test_system_admin_force_withdraw(auth_client: AsyncClient, db: AsyncSession) -> None:
    system_admin = await _create_user(db, user_level=100)
    user = await _create_user(db, user_level=10)
    token = await _create_token(db, user.id)
    _set_admin_cookie(auth_client, system_admin)

    resp = await auth_client.request(
        "DELETE",
        f"/admin/api/v1/users/{user.id}",
        json={"left_reason": "운영 정책 위반"},
    )

    assert resp.status_code == 200
    assert resp.json()["header"]["code"] == "DELETED"

    refreshed_user = await db.scalar(select(User).where(User.id == user.id))
    assert refreshed_user is not None
    assert refreshed_user.del_yn is True
    assert refreshed_user.use_yn is False
    assert refreshed_user.left_at is not None
    assert refreshed_user.left_reason == "운영 정책 위반"

    refreshed_token = await db.scalar(select(UserToken).where(UserToken.id == token.id))
    assert refreshed_token is not None
    assert refreshed_token.is_revoked is True


@pytest.mark.asyncio
async def test_include_deleted_lists_withdrawn_users(
    auth_client: AsyncClient, db: AsyncSession
) -> None:
    admin = await _create_user(db, user_level=70)
    withdrawn = await _create_user(db, user_level=10)
    withdrawn.del_yn = True
    withdrawn.use_yn = False
    withdrawn.left_at = datetime.now(UTC)
    withdrawn.left_reason = "탈퇴"
    await db.commit()
    _set_admin_cookie(auth_client, admin)

    hidden_resp = await auth_client.post(
        "/admin/api/v1/users/list",
        json={"include_deleted": False, "page": 1, "size": 100},
    )
    hidden_ids = [item["id"] for item in hidden_resp.json()["body"]["data"]["items"]]
    assert withdrawn.id not in hidden_ids

    included_resp = await auth_client.post(
        "/admin/api/v1/users/list",
        json={"include_deleted": True, "page": 1, "size": 100},
    )
    included_ids = [item["id"] for item in included_resp.json()["body"]["data"]["items"]]
    assert withdrawn.id in included_ids
