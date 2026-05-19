"""SFR-108: 인증 테스트"""

from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.common.id_generator import next_id
from app.core.security import create_access_token, create_refresh_token_jwt, hash_token
from app.core.user.models import User, UserToken
from tests.conftest import unique_email

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def test_user(db: AsyncSession) -> User:
    """테스트용 유저 생성 — 매 테스트마다 고유 이메일"""
    user_id = await next_id("USR_", db)
    user = User(
        id=user_id,
        email=unique_email(),
        name="테스트유저",
        user_level=10,
        joined_at=datetime.now(UTC),
        created_at=datetime.now(UTC),
        created_by=user_id,
        updated_at=datetime.now(UTC),
        updated_by=user_id,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


# ---------------------------------------------------------------------------
# 보안 모듈 테스트
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_access_token():
    """Access Token 생성 및 디코딩"""
    from app.core.security import decode_token

    token = create_access_token("USR_00000001", user_level=10)
    payload = decode_token(token)
    assert payload["sub"] == "USR_00000001"
    assert payload["level"] == 10
    assert payload["type"] == "access"


@pytest.mark.asyncio
async def test_hash_token_consistent():
    """같은 토큰은 항상 같은 해시 반환"""
    token = "test_refresh_token"
    assert hash_token(token) == hash_token(token)


@pytest.mark.asyncio
async def test_hash_token_different():
    """다른 토큰은 다른 해시 반환"""
    assert hash_token("token_a") != hash_token("token_b")


# ---------------------------------------------------------------------------
# ID 채번 테스트
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_next_id_sequential(db: AsyncSession):
    """ID가 순차적으로 증가하는지 확인"""
    id1 = await next_id("USR_", db)
    id2 = await next_id("USR_", db)
    num1 = int(id1.split("_")[1])
    num2 = int(id2.split("_")[1])
    assert num2 == num1 + 1


@pytest.mark.asyncio
async def test_next_id_format(db: AsyncSession):
    """ID 형식이 PREFIX_00000001 형태인지 확인"""
    user_id = await next_id("USR_", db)
    assert user_id.startswith("USR_")
    assert len(user_id.split("_")[1]) == 8


# ---------------------------------------------------------------------------
# 권한 데코레이터 테스트
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_require_level_no_token(auth_client: AsyncClient):
    """/api/v1/users/me — 토큰 없으면 401"""
    response = await auth_client.get("/api/v1/users/me")
    assert response.status_code == 401
    assert response.json()["header"]["code"] == "UNAUTHORIZED"


@pytest.mark.asyncio
async def test_require_level_valid_token(auth_client: AsyncClient, test_user: User):
    """/api/v1/users/me — 유효한 토큰이면 200"""
    access_token = create_access_token(test_user.id, user_level=test_user.user_level)
    auth_client.cookies.set("access_token", access_token)
    response = await auth_client.get("/api/v1/users/me")
    assert response.status_code == 200
    data = response.json()
    assert data["header"]["success"] is True
    assert data["body"]["data"]["user_id"] == test_user.id


@pytest.mark.asyncio
async def test_require_level_ai_agent_blocked(auth_client: AsyncClient):
    """AI 에이전트 계정(USR_00000000)으로 /users/me 접근 → 403"""
    access_token = create_access_token("USR_00000000", user_level=10)
    auth_client.cookies.set("access_token", access_token)
    response = await auth_client.get("/api/v1/users/me")
    assert response.status_code == 403


# ---------------------------------------------------------------------------
# 토큰 갱신 테스트
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_refresh_no_token(auth_client: AsyncClient):
    """/auth/refresh — 토큰 없으면 401"""
    response = await auth_client.post("/auth/refresh")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_revoked_token(auth_client: AsyncClient, test_user: User, db: AsyncSession):
    """/auth/refresh — revoked 토큰 재사용 시 401"""
    refresh_jwt = create_refresh_token_jwt(test_user.id)
    token = UserToken(
        id=await next_id("UTKN_", db),
        user_id=test_user.id,
        token_hash=hash_token(refresh_jwt),
        expires_at=datetime.now(UTC) + timedelta(days=30),
        is_revoked=True,  # 이미 revoked
        created_at=datetime.now(UTC) - timedelta(minutes=5),  # grace period 초과
        created_by=test_user.id,
    )
    db.add(token)
    await db.commit()

    auth_client.cookies.set("refresh_token", refresh_jwt)
    response = await auth_client.post("/auth/refresh")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_expired_token(auth_client: AsyncClient, test_user: User, db: AsyncSession):
    """/auth/refresh — 만료된 토큰은 401"""
    refresh_jwt = create_refresh_token_jwt(test_user.id)
    token = UserToken(
        id=await next_id("UTKN_", db),
        user_id=test_user.id,
        token_hash=hash_token(refresh_jwt),
        expires_at=datetime.now(UTC) - timedelta(days=1),  # 만료됨
        is_revoked=False,
        created_at=datetime.now(UTC) - timedelta(days=31),
        created_by=test_user.id,
    )
    db.add(token)
    await db.commit()

    auth_client.cookies.set("refresh_token", refresh_jwt)
    response = await auth_client.post("/auth/refresh")
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# 로그아웃 테스트
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_logout_success(auth_client: AsyncClient):
    """/auth/logout — 토큰 없어도 200 (관대한 처리)"""
    response = await auth_client.post("/auth/logout")
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# dev 토큰 테스트
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_dev_token_not_found(auth_client: AsyncClient):
    """/auth/dev/token — 존재하지 않는 user_id는 404"""
    response = await auth_client.post(
        "/auth/dev/token",
        json={"user_id": "USR_99999999"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_dev_token_success(auth_client: AsyncClient, test_user: User):
    """/auth/dev/token — 유효한 user_id면 토큰 발급"""
    response = await auth_client.post(
        "/auth/dev/token",
        json={"user_id": test_user.id},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


# ---------------------------------------------------------------------------
# OAuth state 테스트
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_google_callback_invalid_state(auth_client: AsyncClient):
    """/auth/google/callback — state 불일치 시 400"""
    auth_client.cookies.set("oauth_state", "correct_state")
    response = await auth_client.get(
        "/auth/google/callback",
        params={"code": "some_code", "state": "wrong_state"},
    )
    assert response.status_code == 400
    assert response.json()["header"]["code"] == "INVALID_STATE"


@pytest.mark.asyncio
async def test_kakao_callback_invalid_state(auth_client: AsyncClient):
    """/auth/kakao/callback — state 불일치 시 400"""
    auth_client.cookies.set("oauth_state", "correct_state")
    response = await auth_client.get(
        "/auth/kakao/callback",
        params={"code": "some_code", "state": "wrong_state"},
    )
    assert response.status_code == 400
    assert response.json()["header"]["code"] == "INVALID_STATE"
