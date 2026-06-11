"""Auth 도메인 DB 쿼리"""

from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import LoginLog
from app.core.user.models import User, UserOAuth, UserToken


class AuthRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # User
    # ------------------------------------------------------------------

    async def get_user_by_email(self, email: str) -> User | None:
        result = await self.db.execute(
            select(User).where(User.email == email, User.del_yn.is_(False))
        )
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: str) -> User | None:
        result = await self.db.execute(
            select(User).where(User.id == user_id, User.del_yn.is_(False))
        )
        return result.scalar_one_or_none()

    async def create_user(self, user: User) -> User:
        self.db.add(user)
        await self.db.flush()
        return user

    async def update_user_last_login(self, user_id: str) -> None:
        await self.db.execute(
            update(User).where(User.id == user_id).values(last_login_at=datetime.now(UTC))
        )

    # ------------------------------------------------------------------
    # UserOAuth
    # ------------------------------------------------------------------

    async def get_oauth(self, provider: str, provider_user_id: str) -> UserOAuth | None:
        result = await self.db.execute(
            select(UserOAuth).where(
                UserOAuth.provider == provider,
                UserOAuth.provider_user_id == provider_user_id,
                UserOAuth.del_yn.is_(False),
            )
        )
        return result.scalar_one_or_none()

    async def create_oauth(self, oauth: UserOAuth) -> UserOAuth:
        self.db.add(oauth)
        await self.db.flush()
        return oauth

    # ------------------------------------------------------------------
    # UserToken (Refresh Token)
    # ------------------------------------------------------------------

    async def get_token_by_hash(self, token_hash: str) -> UserToken | None:
        # jti 도입 이전 발급분은 동일 해시가 중복 적재됐을 수 있다.
        # 활성(is_revoked=False) 토큰 우선, 최신순으로 1건만 사용한다.
        result = await self.db.execute(
            select(UserToken)
            .where(UserToken.token_hash == token_hash)
            .order_by(UserToken.is_revoked.asc(), UserToken.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def create_token(self, token: UserToken) -> UserToken:
        self.db.add(token)
        await self.db.flush()
        return token

    async def revoke_token(self, token: UserToken) -> None:
        token.is_revoked = True

    async def revoke_tokens_by_hash(self, token_hash: str) -> None:
        # 동일 해시 중복 행이 있어도 전부 무효화 (로그아웃용)
        await self.db.execute(
            update(UserToken)
            .where(UserToken.token_hash == token_hash, UserToken.is_revoked.is_(False))
            .values(is_revoked=True)
        )

    async def revoke_all_user_tokens(self, user_id: str) -> None:
        await self.db.execute(
            update(UserToken)
            .where(UserToken.user_id == user_id, UserToken.is_revoked.is_(False))
            .values(is_revoked=True)
        )

    # ------------------------------------------------------------------
    # LoginLog
    # ------------------------------------------------------------------

    async def create_login_log(self, log: LoginLog) -> None:
        self.db.add(log)
        await self.db.flush()
