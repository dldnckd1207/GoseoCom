"""Auth 서비스 — OAuth UPSERT, 토큰 발급/갱신/로그아웃"""

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
    ) -> tuple[str, str]:
        ip_address = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "")

        try:
            user = await self._upsert_user_and_oauth(
                provider, provider_user_id, email, name, profile_image_url
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
        except Exception as e:
            await self.db.rollback()
            await self._log(None, provider, LoginResult.FAIL, ip_address, str(e))
            raise

    async def _upsert_user_and_oauth(
        self,
        provider: str,
        provider_user_id: str,
        email: str | None,
        name: str,
        profile_image_url: str | None,
    ) -> User:
        oauth = await self.repo.get_oauth(provider, provider_user_id)
        user = (
            await self.repo.get_user_by_id(oauth.user_id)
            if oauth
            # 이메일이 있을 때만 email로 계정 연동 시도 (없으면 None → 신규 생성)
            else (await self.repo.get_user_by_email(email) if email else None)
        )
        now = datetime.now(UTC)

        if not user:
            user_id = await next_id("USR_", self.db)
            # TODO(#106): 카카오 비즈앱 전환 후 이메일 필수 검증 추가
            # 현재 이메일 미동의 사용자는 user_id 기반 placeholder 사용
            actual_email = email if email else f"{user_id}@haedok-ai.com"
            user = User(
                id=user_id,
                email=actual_email,
                name=name,
                profile_image_url=profile_image_url,
                user_level=self._resolve_user_level(email),
                joined_at=now,
                created_at=now,
                created_by=user_id,
                updated_at=now,
                updated_by=user_id,
            )
            await self.repo.create_user(user)
        elif self._should_promote_to_initial_admin(user, email):
            user.user_level = UserRole.ADMIN.value
            user.updated_at = now
            user.updated_by = user.id

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

    def _resolve_user_level(self, email: str | None) -> int:
        if email and email in settings.admin_emails:
            return UserRole.ADMIN.value
        return UserRole.USER.value

    def _should_promote_to_initial_admin(self, user: User, email: str | None) -> bool:
        return bool(
            email and email in settings.admin_emails and user.user_level < UserRole.ADMIN.value
        )

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
            token = await self.repo.get_token_by_hash(hash_token(refresh_jwt))
            if token and not token.is_revoked:
                await self.repo.revoke_token(token)
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
