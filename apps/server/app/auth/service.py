"""Auth 서비스 — OAuth UPSERT, 토큰 발급/갱신/로그아웃"""

import logging
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import LoginLog
from app.auth.repository import AuthRepository
from app.config import settings
from app.core.common.enums import LoginResult, UserRole
from app.core.common.id_generator import next_id
from app.core.security import (
    create_access_token,
    create_refresh_token_jwt,
    hash_token,
)
from app.core.user.models import User, UserOAuth, UserToken

logger = logging.getLogger(__name__)

ROTATION_GRACE_SECONDS = 30


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self.repo = AuthRepository(db)
        self.db = db

    async def login_or_register(
        self,
        provider: str,
        provider_user_id: str,
        email: str
        | None,  # TODO(#106): 카카오 비즈앱 전환 후 email 필수화 (현재 이메일 미동의 사용자 허용)
        name: str,
        profile_image_url: str | None,
        request: Request,
        email_verified: bool = False,
    ) -> tuple[str, str]:
        ip_address = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "")

        try:
            user = await self._upsert_user_and_oauth(
                provider, provider_user_id, email, name, profile_image_url, email_verified
            )

            if user.del_yn and user.left_at:
                cutoff = user.left_at + timedelta(days=90)
                if datetime.now(UTC) < cutoff:
                    await self._log(
                        None, provider, LoginResult.FAIL, ip_address, "탈퇴 후 90일 이내"
                    )
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail={
                            "code": "WITHDRAWN_USER",
                            "message": "탈퇴 후 90일 이내 재가입이 불가합니다.",
                        },
                    )

            # UBR-04: use_yn=false 계정 로그인 거부
            if not user.use_yn:
                await self._log(None, provider, LoginResult.FAIL, ip_address, "비활성 계정")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={"code": "ACCOUNT_DISABLED", "message": "비활성화된 계정입니다."},
                )

            if user.id == settings.ai_agent_user_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

            # UBR-05: block_yn=true는 로그인 허용, JWT에 blocked 클레임으로 서비스 이용 제한
            access_token = create_access_token(
                user.id, user.user_level, user_name=user.name, blocked=user.block_yn
            )
            refresh_jwt = create_refresh_token_jwt(user.id)
            now = datetime.now(UTC)

            await self.repo.create_token(
                UserToken(
                    id=await next_id("UTKN_", self.db),
                    user_id=user.id,
                    token_hash=hash_token(refresh_jwt),
                    expires_at=now + timedelta(days=settings.jwt_refresh_token_expire_days),
                    created_at=now,
                    created_by=user.id,
                    user_agent=user_agent,
                    ip_address=ip_address,
                )
            )

            await self.repo.update_user_last_login(user.id)
            await self._log(user.id, provider, LoginResult.SUCCESS, ip_address)
            await self.db.commit()
            return access_token, refresh_jwt

        except HTTPException:
            await self.db.rollback()
            raise
        except Exception:
            # 예외 원문은 DB(fail_reason)에 저장하지 않고 표준 코드만 기록한다(점검보고서 #9).
            # 상세 원인은 서버 로그로만 남긴다(PII/내부 구현 노출 방지).
            logger.exception("로그인 처리 중 예기치 못한 오류 (provider=%s)", provider)
            await self.db.rollback()
            await self._log(None, provider, LoginResult.FAIL, ip_address, "INTERNAL_ERROR")
            raise

    async def _upsert_user_and_oauth(
        self,
        provider: str,
        provider_user_id: str,
        email: str | None,
        name: str,
        profile_image_url: str | None,
        email_verified: bool = False,
    ) -> User:
        oauth = await self.repo.get_oauth(provider, provider_user_id)
        # 주 로그인 경로는 (provider, provider_user_id) 매칭 — 이메일 미사용.
        # 이메일 기반 기존 계정 연동은 검증된 신뢰 제공자(email_verified)인 경우에만 허용한다.
        # (점검보고서 #3: 미검증 이메일 가장으로 인한 계정 탈취 방지)
        user = (
            await self.repo.get_user_by_id(oauth.user_id)
            if oauth
            else (await self.repo.get_user_by_email(email) if (email and email_verified) else None)
        )
        now = datetime.now(UTC)

        if not user:
            user_id = await next_id("USR_", self.db)
            # 검증된 이메일만 계정 식별자로 저장. 미검증/미동의 시 user_id 기반 placeholder를
            # 사용해 이메일 선점(squatting)으로 인한 추후 연동 탈취를 차단한다.
            actual_email = email if (email and email_verified) else f"{user_id}@haedok-ai.com"
            user = User(
                id=user_id,
                email=actual_email,
                name=name,
                profile_image_url=profile_image_url,
                # 이메일 기반 자동 ADMIN 승격 제거(점검보고서 #3). 항상 USER로 생성하고,
                # 관리자 지정은 시드 마이그레이션/SYSTEM_ADMIN 수동 변경으로 일원화한다.
                user_level=UserRole.USER.value,
                joined_at=now,
                created_at=now,
                created_by=user_id,
                updated_at=now,
                updated_by=user_id,
            )
            await self.repo.create_user(user)

        if not oauth:
            await self.repo.create_oauth(
                UserOAuth(
                    id=await next_id("OAUTH_", self.db),
                    user_id=user.id,
                    provider=provider,
                    provider_user_id=provider_user_id,
                    provider_email=email,
                    created_at=now,
                    created_by=user.id,
                    updated_at=now,
                    updated_by=user.id,
                )
            )

        return user

    async def refresh(self, refresh_jwt: str, request: Request) -> tuple[str, str]:
        token = await self.repo.get_token_by_hash(hash_token(refresh_jwt))

        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "INVALID_TOKEN", "message": "유효하지 않은 토큰입니다."},
            )

        if token.is_revoked:
            grace_cutoff = token.created_at + timedelta(seconds=ROTATION_GRACE_SECONDS)
            if datetime.now(UTC) > grace_cutoff:
                await self.repo.revoke_all_user_tokens(token.user_id)
                await self.db.commit()
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail={
                        "code": "TOKEN_REUSE_DETECTED",
                        "message": "보안 위협이 감지되었습니다. 다시 로그인해주세요.",
                    },
                )

        if token.expires_at < datetime.now(UTC):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "TOKEN_EXPIRED", "message": "토큰이 만료되었습니다."},
            )

        await self.repo.revoke_token(token)

        user = await self.repo.get_user_by_id(token.user_id)
        user_level = user.user_level if user else 10
        user_name = user.name if user else ""
        blocked = user.block_yn if user else False
        new_access = create_access_token(
            token.user_id, user_level, user_name=user_name, blocked=blocked
        )
        new_refresh_jwt = create_refresh_token_jwt(token.user_id)
        now = datetime.now(UTC)

        await self.repo.create_token(
            UserToken(
                id=await next_id("UTKN_", self.db),
                user_id=token.user_id,
                token_hash=hash_token(new_refresh_jwt),
                expires_at=now + timedelta(days=settings.jwt_refresh_token_expire_days),
                created_at=now,
                created_by=token.user_id,
                user_agent=request.headers.get("user-agent", ""),
                ip_address=request.client.host if request.client else "unknown",
            )
        )

        await self.db.commit()
        return new_access, new_refresh_jwt

    async def logout(self, refresh_jwt: str | None) -> None:
        if refresh_jwt:
            await self.repo.revoke_tokens_by_hash(hash_token(refresh_jwt))
            await self.db.commit()

    async def _log(
        self,
        user_id: str | None,
        provider: str,
        result: LoginResult,
        ip_address: str,
        fail_reason: str | None = None,
    ) -> None:
        await self.repo.create_login_log(
            LoginLog(
                user_id=user_id,
                login_id=provider,
                login_type=provider,
                login_result=result.value,
                fail_reason=fail_reason[:255] if fail_reason else None,
                ip_address=ip_address,
                created_at=datetime.now(UTC),
            )
        )
