"""사용자 Repository — DB 쿼리"""

from datetime import UTC, datetime

from sqlalchemy import ColumnElement, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.user.models import User, UserToken
from app.core.user.schemas import AdminUserListRequest


class UserRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def admin_list(self, req: AdminUserListRequest) -> tuple[list[User], int]:
        conditions: list[ColumnElement[bool]] = []
        if not req.include_deleted:
            conditions.append(User.del_yn.is_(False))
        if req.use_yn is not None:
            conditions.append(User.use_yn.is_(req.use_yn))
        if req.block_yn is not None:
            conditions.append(User.block_yn.is_(req.block_yn))
        if req.role == "user":
            conditions.append(User.user_level < 70)
        elif req.role == "admin":
            conditions.append(User.user_level >= 70)
            conditions.append(User.user_level < 100)
        elif req.role == "system_admin":
            conditions.append(User.user_level >= 100)
        if req.keyword:
            keyword = f"%{req.keyword}%"
            conditions.append(or_(User.name.ilike(keyword), User.email.ilike(keyword)))

        base = select(User).where(*conditions).order_by(User.joined_at.desc(), User.id.desc())
        total_result = await self.db.execute(select(func.count()).select_from(base.subquery()))
        total: int = total_result.scalar_one()
        result = await self.db.execute(base.offset((req.page - 1) * req.size).limit(req.size))
        return list(result.scalars().all()), total

    async def get_by_id_for_admin(self, user_id: str, include_deleted: bool = False) -> User | None:
        conditions: list[ColumnElement[bool]] = [User.id == user_id]
        if not include_deleted:
            conditions.append(User.del_yn.is_(False))
        result = await self.db.execute(select(User).where(*conditions))
        return result.scalar_one_or_none()

    async def update_user(self, user: User) -> User:
        await self.db.flush()
        return user

    async def revoke_user_tokens(self, user_id: str) -> None:
        await self.db.execute(
            update(UserToken)
            .where(UserToken.user_id == user_id, UserToken.is_revoked.is_(False))
            .values(is_revoked=True)
        )

    async def soft_withdraw(self, user: User, reason: str, actor_id: str) -> None:
        now = datetime.now(UTC)
        user.del_yn = True
        user.deleted_at = now
        user.deleted_by = actor_id
        user.use_yn = False
        user.left_at = now
        user.left_reason = reason
        user.updated_at = now
        user.updated_by = actor_id
        await self.revoke_user_tokens(user.id)
        await self.db.flush()
