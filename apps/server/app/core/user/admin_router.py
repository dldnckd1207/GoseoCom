"""사용자 관리자 라우터 — /admin/api/v1/users/"""

from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.common.decorators.require_level import require_level
from app.core.common.enums import UserRole
from app.core.common.response import ApiResponse, PageData
from app.core.user.schemas import (
    AdminUserDetailResponse,
    AdminUserForceWithdrawRequest,
    AdminUserListItemResponse,
    AdminUserListRequest,
    AdminUserUpdateRequest,
)
from app.core.user.service import UserService
from app.db.session import get_db

admin_router = APIRouter(prefix="/admin/api/v1/users", tags=["admin-users"])

_ERR_401_UNAUTHORIZED = {
    "description": "인증 필요",
    "content": {
        "application/json": {
            "example": {
                "header": {
                    "success": False,
                    "code": "UNAUTHORIZED",
                    "message": "로그인이 필요합니다.",
                },
                "body": {"data": None},
            }
        }
    },
}

_ERR_403_FORBIDDEN = {
    "description": "권한 없음",
    "content": {
        "application/json": {
            "examples": {
                "forbidden": {
                    "summary": "권한 부족",
                    "value": {
                        "header": {
                            "success": False,
                            "code": "FORBIDDEN",
                            "message": "접근 권한이 없습니다.",
                        },
                        "body": {"data": None},
                    },
                },
                "system_admin_only": {
                    "summary": "슈퍼관리자 전용",
                    "value": {
                        "header": {
                            "success": False,
                            "code": "SYSTEM_ADMIN_ONLY",
                            "message": "슈퍼관리자만 수행할 수 있습니다.",
                        },
                        "body": {"data": None},
                    },
                },
            }
        }
    },
}

_ERR_400_SELF = {
    "description": "본인 계정 보호",
    "content": {
        "application/json": {
            "example": {
                "header": {
                    "success": False,
                    "code": "SELF_PROTECTION",
                    "message": "본인 계정은 보호되어 변경할 수 없습니다.",
                },
                "body": {"data": None},
            }
        }
    },
}

_ERR_404_USER = {
    "description": "사용자 없음",
    "content": {
        "application/json": {
            "example": {
                "header": {
                    "success": False,
                    "code": "USER_NOT_FOUND",
                    "message": "사용자를 찾을 수 없습니다.",
                },
                "body": {"data": None},
            }
        }
    },
}


@admin_router.post(
    "/list",
    summary="사용자 목록 조회 (관리자)",
    response_model=ApiResponse[PageData[AdminUserListItemResponse]],
    status_code=status.HTTP_200_OK,
    responses={401: _ERR_401_UNAUTHORIZED, 403: _ERR_403_FORBIDDEN},
)
async def admin_list_users(
    req: AdminUserListRequest,
    payload: dict[str, Any] = require_level(UserRole.ADMIN),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[PageData[AdminUserListItemResponse]]:
    service = UserService(db)
    data = await service.admin_list_users(req, payload)
    return ApiResponse.success(data)


@admin_router.get(
    "/{user_id}",
    summary="사용자 상세 조회 (관리자)",
    response_model=ApiResponse[AdminUserDetailResponse],
    status_code=status.HTTP_200_OK,
    responses={401: _ERR_401_UNAUTHORIZED, 403: _ERR_403_FORBIDDEN, 404: _ERR_404_USER},
)
async def admin_get_user(
    user_id: str,
    payload: dict[str, Any] = require_level(UserRole.ADMIN),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[AdminUserDetailResponse]:
    service = UserService(db)
    data = await service.admin_get_user(user_id, payload)
    return ApiResponse.success(data)


@admin_router.put(
    "/{user_id}",
    summary="사용자 상태/권한 수정 (관리자)",
    response_model=ApiResponse[AdminUserDetailResponse],
    status_code=status.HTTP_200_OK,
    responses={
        400: _ERR_400_SELF,
        401: _ERR_401_UNAUTHORIZED,
        403: _ERR_403_FORBIDDEN,
        404: _ERR_404_USER,
    },
)
async def admin_update_user(
    user_id: str,
    req: AdminUserUpdateRequest,
    payload: dict[str, Any] = require_level(UserRole.ADMIN),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[AdminUserDetailResponse]:
    service = UserService(db)
    data = await service.admin_update_user(user_id, req, payload)
    return ApiResponse.updated(data, message="사용자 정보가 수정되었습니다.")


@admin_router.delete(
    "/{user_id}",
    summary="사용자 강제 탈퇴 (관리자)",
    response_model=ApiResponse[None],
    status_code=status.HTTP_200_OK,
    responses={
        400: _ERR_400_SELF,
        401: _ERR_401_UNAUTHORIZED,
        403: _ERR_403_FORBIDDEN,
        404: _ERR_404_USER,
    },
)
async def admin_force_withdraw_user(
    user_id: str,
    req: AdminUserForceWithdrawRequest,
    payload: dict[str, Any] = require_level(UserRole.ADMIN),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[None]:
    service = UserService(db)
    await service.admin_force_withdraw_user(user_id, req, payload)
    return ApiResponse.deleted("사용자가 강제 탈퇴 처리되었습니다.")
