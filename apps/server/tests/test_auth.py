"""SFR-108: 인증 테스트"""

from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from app.auth.service import AuthService
from app.core.common.enums import UserRole
from app.core.common.id_generator import next_id
from app.core.security import (
    create_access_token,
    create_refresh_token_jwt,
    decode_token,
    hash_token,
)
from app.core.user.models import User, UserToken
from tests.conftest import unique_email


def _fake_request() -> Request:
    """서비스 직접 호출용 최소 ASGI Request (client/headers만 사용)."""
    return Request(
        {
            "type": "http",
            "headers": [(b"user-agent", b"pytest")],
            "client": ("127.0.0.1", 12345),
        }
    )


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
async def test_create_access_token() -> None:
    """Access Token 생성 및 디코딩"""
    from app.core.security import decode_token

    token = create_access_token("USR_00000001", user_level=10)
    payload = decode_token(token)
    assert payload["sub"] == "USR_00000001"
    assert payload["level"] == 10
    assert payload["type"] == "access"


@pytest.mark.asyncio
async def test_hash_token_consistent() -> None:
    """같은 토큰은 항상 같은 해시 반환"""
    token = "test_refresh_token"
    assert hash_token(token) == hash_token(token)


@pytest.mark.asyncio
async def test_hash_token_different() -> None:
    """다른 토큰은 다른 해시 반환"""
    assert hash_token("token_a") != hash_token("token_b")


# ---------------------------------------------------------------------------
# ID 채번 테스트
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_next_id_sequential(db: AsyncSession) -> None:
    """ID가 순차적으로 증가하는지 확인"""
    id1 = await next_id("USR_", db)
    id2 = await next_id("USR_", db)
    num1 = int(id1.split("_")[1])
    num2 = int(id2.split("_")[1])
    assert num2 == num1 + 1


@pytest.mark.asyncio
async def test_next_id_format(db: AsyncSession) -> None:
    """ID 형식이 PREFIX_00000001 형태인지 확인"""
    user_id = await next_id("USR_", db)
    assert user_id.startswith("USR_")
    assert len(user_id.split("_")[1]) == 8


# ---------------------------------------------------------------------------
# 권한 데코레이터 테스트
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_require_level_no_token(auth_client: AsyncClient) -> None:
    """/api/v1/users/me — 토큰 없으면 401"""
    response = await auth_client.get("/api/v1/users/me")
    assert response.status_code == 401
    assert response.json()["header"]["code"] == "UNAUTHORIZED"


@pytest.mark.asyncio
async def test_require_level_valid_token(auth_client: AsyncClient, test_user: User) -> None:
    """/api/v1/users/me — 유효한 토큰이면 200"""
    access_token = create_access_token(test_user.id, user_level=test_user.user_level)
    auth_client.cookies.set("access_token", access_token)
    response = await auth_client.get("/api/v1/users/me")
    assert response.status_code == 200
    data = response.json()
    assert data["header"]["success"] is True
    assert data["body"]["data"]["user_id"] == test_user.id


@pytest.mark.asyncio
async def test_require_level_ai_agent_blocked(auth_client: AsyncClient) -> None:
    """AI 에이전트 계정(USR_00000000)으로 /users/me 접근 → 403"""
    access_token = create_access_token("USR_00000000", user_level=10)
    auth_client.cookies.set("access_token", access_token)
    response = await auth_client.get("/api/v1/users/me")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_blocked_user_rejected_immediately(
    auth_client: AsyncClient, test_user: User, db: AsyncSession
) -> None:
    """차단(block_yn) 즉시 반영: 차단 전 발급된 토큰(blocked=False)도 즉시 403 (점검보고서 #8)"""
    # 토큰은 차단 전 상태(blocked=False)로 발급
    access_token = create_access_token(test_user.id, user_level=10, blocked=False)
    # DB에서 사용자 차단
    test_user.block_yn = True
    await db.commit()

    auth_client.cookies.set("access_token", access_token)
    response = await auth_client.get("/api/v1/users/me")
    assert response.status_code == 403
    assert response.json()["header"]["code"] == "ACCOUNT_BLOCKED"


@pytest.mark.asyncio
async def test_disabled_user_rejected_immediately(
    auth_client: AsyncClient, test_user: User, db: AsyncSession
) -> None:
    """비활성(use_yn=false) 즉시 반영: 기존 토큰으로도 즉시 403 (점검보고서 #8)"""
    access_token = create_access_token(test_user.id, user_level=10)
    test_user.use_yn = False
    await db.commit()

    auth_client.cookies.set("access_token", access_token)
    response = await auth_client.get("/api/v1/users/me")
    assert response.status_code == 403
    assert response.json()["header"]["code"] == "ACCOUNT_DISABLED"


# ---------------------------------------------------------------------------
# 토큰 갱신 테스트
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_refresh_no_token(auth_client: AsyncClient) -> None:
    """/auth/refresh — 토큰 없으면 401"""
    response = await auth_client.post("/auth/refresh")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_revoked_token(
    auth_client: AsyncClient, test_user: User, db: AsyncSession
) -> None:
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
async def test_refresh_expired_token(
    auth_client: AsyncClient, test_user: User, db: AsyncSession
) -> None:
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
async def test_logout_success(auth_client: AsyncClient) -> None:
    """/auth/logout — 토큰 없어도 200 (관대한 처리)"""
    response = await auth_client.post("/auth/logout")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_refresh_jwt_unique_same_second() -> None:
    """같은 유저가 같은 초에 발급받아도 jti로 토큰 원문이 달라야 한다"""
    jwt_a = create_refresh_token_jwt("USR_00000001")
    jwt_b = create_refresh_token_jwt("USR_00000001")
    assert jwt_a != jwt_b
    assert hash_token(jwt_a) != hash_token(jwt_b)


@pytest.mark.asyncio
async def test_logout_with_duplicate_token_hash(
    auth_client: AsyncClient, test_user: User, db: AsyncSession
) -> None:
    """/auth/logout — jti 도입 이전 중복 적재된 동일 해시 토큰이 있어도 500 없이 전부 revoke"""
    refresh_jwt = create_refresh_token_jwt(test_user.id)
    tokens = []
    for _ in range(2):
        token = UserToken(
            id=await next_id("UTKN_", db),
            user_id=test_user.id,
            token_hash=hash_token(refresh_jwt),
            expires_at=datetime.now(UTC) + timedelta(days=30),
            is_revoked=False,
            created_at=datetime.now(UTC),
            created_by=test_user.id,
        )
        db.add(token)
        tokens.append(token)
    await db.commit()

    auth_client.cookies.set("refresh_token", refresh_jwt)
    response = await auth_client.post("/auth/logout")
    assert response.status_code == 200

    for token in tokens:
        await db.refresh(token)
        assert token.is_revoked is True


@pytest.mark.asyncio
async def test_refresh_with_duplicate_token_hash(
    auth_client: AsyncClient, test_user: User, db: AsyncSession
) -> None:
    """/auth/refresh — 동일 해시 중복(활성+revoked 혼재) 시 활성 토큰 우선으로 정상 갱신"""
    refresh_jwt = create_refresh_token_jwt(test_user.id)
    for is_revoked in (True, False):
        db.add(
            UserToken(
                id=await next_id("UTKN_", db),
                user_id=test_user.id,
                token_hash=hash_token(refresh_jwt),
                expires_at=datetime.now(UTC) + timedelta(days=30),
                is_revoked=is_revoked,
                created_at=datetime.now(UTC) - timedelta(minutes=5),
                created_by=test_user.id,
            )
        )
    await db.commit()

    auth_client.cookies.set("refresh_token", refresh_jwt)
    response = await auth_client.post("/auth/refresh")
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# dev 토큰 테스트
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_dev_token_not_found(auth_client: AsyncClient) -> None:
    """/auth/dev/token — 존재하지 않는 user_id는 404"""
    response = await auth_client.post(
        "/auth/dev/token",
        json={"user_id": "USR_99999999"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_dev_token_success(auth_client: AsyncClient, test_user: User) -> None:
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
async def test_google_callback_invalid_state(auth_client: AsyncClient) -> None:
    """/auth/google/callback — state 불일치 시 400"""
    auth_client.cookies.set("oauth_state", "correct_state")
    response = await auth_client.get(
        "/auth/google/callback",
        params={"code": "some_code", "state": "wrong_state"},
    )
    assert response.status_code == 400
    assert response.json()["header"]["code"] == "INVALID_STATE"


@pytest.mark.asyncio
async def test_kakao_callback_invalid_state(auth_client: AsyncClient) -> None:
    """/auth/kakao/callback — state 불일치 시 400"""
    auth_client.cookies.set("oauth_state", "correct_state")
    response = await auth_client.get(
        "/auth/kakao/callback",
        params={"code": "some_code", "state": "wrong_state"},
    )
    assert response.status_code == 400
    assert response.json()["header"]["code"] == "INVALID_STATE"


# ---------------------------------------------------------------------------
# 이메일 기반 계정 연동 / 자동 관리자 승격 차단 (점검보고서 #3)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_unverified_email_does_not_link_to_existing(db: AsyncSession) -> None:
    """미검증 이메일 로그인은 동일 이메일의 기존 계정에 연동되지 않고 신규 생성된다."""
    email = unique_email()
    existing_id = await next_id("USR_", db)
    existing = User(
        id=existing_id,
        email=email,
        name="기존유저",
        user_level=UserRole.USER.value,
        joined_at=datetime.now(UTC),
        created_at=datetime.now(UTC),
        created_by=existing_id,
        updated_at=datetime.now(UTC),
        updated_by=existing_id,
    )
    db.add(existing)
    await db.commit()

    service = AuthService(db)
    access_token, _ = await service.login_or_register(
        provider="KAKAO",
        provider_user_id=f"kakao-{existing_id}",
        email=email,
        email_verified=False,  # 미검증 제공자
        name="가장유저",
        profile_image_url=None,
        request=_fake_request(),
    )
    payload = decode_token(access_token)
    # 기존 계정에 연동되지 않고 별도의 신규 계정으로 생성되어야 함
    assert payload["sub"] != existing_id


@pytest.mark.asyncio
async def test_unverified_email_admin_impersonation_no_promotion(db: AsyncSession) -> None:
    """관리자 이메일을 미검증 제공자로 가장 로그인해도 USER로만 생성된다(자동 승격 없음)."""
    admin_email = unique_email()
    admin_id = await next_id("USR_", db)
    admin = User(
        id=admin_id,
        email=admin_email,
        name="관리자",
        user_level=UserRole.ADMIN.value,  # 기존 관리자
        joined_at=datetime.now(UTC),
        created_at=datetime.now(UTC),
        created_by=admin_id,
        updated_at=datetime.now(UTC),
        updated_by=admin_id,
    )
    db.add(admin)
    await db.commit()

    service = AuthService(db)
    access_token, _ = await service.login_or_register(
        provider="KAKAO",
        provider_user_id=f"kakao-imposter-{admin_id}",
        email=admin_email,
        email_verified=False,
        name="가장공격자",
        profile_image_url=None,
        request=_fake_request(),
    )
    payload = decode_token(access_token)
    assert payload["sub"] != admin_id  # 관리자 계정 탈취 불가
    assert payload["level"] == UserRole.USER.value  # 자동 승격 없음


@pytest.mark.asyncio
async def test_verified_email_links_to_existing(db: AsyncSession) -> None:
    """검증된 이메일은 동일 이메일의 기존 계정에 연동된다."""
    email = unique_email()
    existing_id = await next_id("USR_", db)
    existing = User(
        id=existing_id,
        email=email,
        name="기존유저",
        user_level=UserRole.USER.value,
        joined_at=datetime.now(UTC),
        created_at=datetime.now(UTC),
        created_by=existing_id,
        updated_at=datetime.now(UTC),
        updated_by=existing_id,
    )
    db.add(existing)
    await db.commit()

    service = AuthService(db)
    access_token, _ = await service.login_or_register(
        provider="GOOGLE",
        provider_user_id=f"google-{existing_id}",
        email=email,
        email_verified=True,  # 검증된 신뢰 제공자
        name="기존유저",
        profile_image_url=None,
        request=_fake_request(),
    )
    payload = decode_token(access_token)
    assert payload["sub"] == existing_id  # 기존 계정에 연동


@pytest.mark.asyncio
async def test_verified_email_cross_provider_same_account(db: AsyncSession) -> None:
    """동일인이 검증 이메일로 Google→Kakao 로그인 시 같은 계정으로 연동된다(D-1)."""
    email = unique_email()
    service = AuthService(db)

    access1, _ = await service.login_or_register(
        provider="GOOGLE",
        provider_user_id=f"google-{email}",
        email=email,
        email_verified=True,
        name="동일인",
        profile_image_url=None,
        request=_fake_request(),
    )
    access2, _ = await service.login_or_register(
        provider="KAKAO",
        provider_user_id=f"kakao-{email}",
        email=email,
        email_verified=True,
        name="동일인",
        profile_image_url=None,
        request=_fake_request(),
    )
    assert decode_token(access1)["sub"] == decode_token(access2)["sub"]
