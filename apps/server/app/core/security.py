"""JWT 서명/검증 및 토큰 해시 — 공통 보안 모듈"""

import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta

import jwt

from app.config import settings

# ---------------------------------------------------------------------------
# JWT
# ---------------------------------------------------------------------------


def create_access_token(
    user_id: str, user_level: int, user_name: str = "", blocked: bool = False
) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    return jwt.encode(
        {
            "sub": user_id,
            "level": user_level,
            "name": user_name,
            "blocked": blocked,
            "exp": expire,
            "type": "access",
        },
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def create_refresh_token_jwt(user_id: str) -> str:
    expire = datetime.now(UTC) + timedelta(days=settings.jwt_refresh_token_expire_days)
    return jwt.encode(
        {"sub": user_id, "exp": expire, "type": "refresh"},
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_token(token: str) -> dict[str, object]:
    """토큰 디코딩. 만료/유효하지 않으면 jwt.PyJWTError 발생."""
    return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])


# ---------------------------------------------------------------------------
# Refresh Token 해시 (HMAC-SHA256)
# ---------------------------------------------------------------------------


def hash_token(token: str) -> str:
    """Refresh Token을 HMAC-SHA256으로 해시. DB 저장용."""
    return hmac.new(
        settings.app_secret_key.encode(),
        token.encode(),
        hashlib.sha256,
    ).hexdigest()


def generate_raw_refresh_token() -> str:
    """안전한 랜덤 Refresh Token 원문 생성."""
    return secrets.token_urlsafe(64)
