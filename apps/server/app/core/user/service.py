"""사용자 Service — 관리자 사용자 관리 비즈니스 로직"""

from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.common.enums import UserRole
from app.core.common.response import PageData
from app.core.user.models import User
from app.core.user.repository import UserRepository
from app.core.user.schemas import (
    AdminUserDetailResponse,
    AdminUserForceWithdrawRequest,
    AdminUserListItemResponse,
    AdminUserListRequest,
    AdminUserUpdateRequest,
)


class UserService:
    def __init__(self, db: AsyncSession) -> None:
        self.repo = UserRepository(db)
        self.db = db

    async def admin_list_users(
        self, req: AdminUserListRequest, actor: dict[str, Any]
    ) -> PageData[AdminUserListItemResponse]:
        users, total = await self.repo.admin_list(req)
        actor_id = str(actor.get("sub", ""))
        return PageData(
            items=[self._to_list_item(user, actor_id) for user in users],
            total=total,
            page=req.page,
            size=req.size,
        )

    async def admin_get_user(self, user_id: str, actor: dict[str, Any]) -> AdminUserDetailResponse:
        user = await self.repo.get_by_id_for_admin(user_id, include_deleted=True)
        if not user:
            raise self._not_found()
        return self._to_detail(user, str(actor.get("sub", "")))

    async def admin_update_user(
        self, user_id: str, req: AdminUserUpdateRequest, actor: dict[str, Any]
    ) -> AdminUserDetailResponse:
        user = await self.repo.get_by_id_for_admin(user_id)
        if not user:
            raise self._not_found()

        actor_id = str(actor.get("sub", ""))
        actor_level = int(actor.get("level", 0))
        self._ensure_can_update(user, req, actor_id, actor_level)

        should_revoke_tokens = False
        update_fields = req.model_dump(exclude_none=True)
        now = datetime.now(UTC)

        if "user_level" in update_fields:
            user.user_level = update_fields["user_level"]
        if "use_yn" in update_fields:
            user.use_yn = update_fields["use_yn"]
            if update_fields["use_yn"] is False:
                should_revoke_tokens = True
        if "block_yn" in update_fields:
            user.block_yn = update_fields["block_yn"]
            if update_fields["block_yn"] is True:
                user.blocked_at = now
                user.blocked_by = actor_id
                should_revoke_tokens = True
            else:
                user.blocked_at = None
                user.blocked_by = None

        user.updated_at = now
        user.updated_by = actor_id
        if should_revoke_tokens:
            await self.repo.revoke_user_tokens(user.id)

        updated = await self.repo.update_user(user)
        await self.db.commit()
        await self.db.refresh(updated)
        return self._to_detail(updated, actor_id)

    async def admin_force_withdraw_user(
        self, user_id: str, req: AdminUserForceWithdrawRequest, actor: dict[str, Any]
    ) -> None:
        user = await self.repo.get_by_id_for_admin(user_id)
        if not user:
            raise self._not_found()

        actor_id = str(actor.get("sub", ""))
        actor_level = int(actor.get("level", 0))
        if actor_id == user.id:
            raise self._self_protection()
        if actor_level < UserRole.SYSTEM_ADMIN.value:
            raise self._system_admin_only()

        await self.repo.soft_withdraw(user, req.left_reason.strip(), actor_id)
        await self.db.commit()

    def _ensure_can_update(
        self, user: User, req: AdminUserUpdateRequest, actor_id: str, actor_level: int
    ) -> None:
        update_fields = req.model_dump(exclude_none=True)
        changed_fields = {
            field for field, value in update_fields.items() if getattr(user, field) != value
        }
        if actor_id == user.id and changed_fields:
            raise self._self_protection()

        if "user_level" in changed_fields and actor_level < UserRole.SYSTEM_ADMIN.value:
            raise self._system_admin_only()

        status_fields = {"use_yn", "block_yn"} & set(update_fields)
        if (
            status_fields
            and user.user_level >= UserRole.SYSTEM_ADMIN.value
            and actor_level < UserRole.SYSTEM_ADMIN.value
        ):
            raise self._system_admin_only()

    def _to_list_item(self, user: User, actor_id: str) -> AdminUserListItemResponse:
        return AdminUserListItemResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            profile_image_url=user.profile_image_url,
            user_level=user.user_level,
            role_label=self._role_label(user.user_level),
            use_yn=user.use_yn,
            block_yn=user.block_yn,
            joined_at=user.joined_at,
            last_login_at=user.last_login_at,
            left_at=user.left_at,
            del_yn=user.del_yn,
            is_self=user.id == actor_id,
        )

    def _to_detail(self, user: User, actor_id: str) -> AdminUserDetailResponse:
        return AdminUserDetailResponse(
            **self._to_list_item(user, actor_id).model_dump(),
            blocked_at=user.blocked_at,
            blocked_by=user.blocked_by,
            left_reason=user.left_reason,
        )

    def _role_label(self, user_level: int) -> str:
        if user_level >= UserRole.SYSTEM_ADMIN.value:
            return "슈퍼관리자"
        if user_level >= UserRole.ADMIN.value:
            return "관리자"
        return "사용자"

    def _not_found(self) -> HTTPException:
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "USER_NOT_FOUND", "message": "사용자를 찾을 수 없습니다."},
        )

    def _system_admin_only(self) -> HTTPException:
        return HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "SYSTEM_ADMIN_ONLY", "message": "슈퍼관리자만 수행할 수 있습니다."},
        )

    def _self_protection(self) -> HTTPException:
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "SELF_PROTECTION",
                "message": "본인 계정은 보호되어 변경할 수 없습니다.",
            },
        )
