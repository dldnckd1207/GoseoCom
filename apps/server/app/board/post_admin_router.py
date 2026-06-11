"""게시글 관리자 라우터 — /admin/api/v1/posts/"""

from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.board.post_schemas import (
    AdminPostDetailResponse,
    AdminPostListRequest,
    AdminPostSummaryResponse,
)
from app.board.post_service import PostService
from app.core.common.decorators.require_level import require_level
from app.core.common.enums import UserRole
from app.core.common.response import ApiResponse, PageData
from app.db.session import get_db

admin_router = APIRouter(prefix="/admin/api/v1/posts", tags=["admin-posts"])

_ERR_401 = {
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
_ERR_403 = {
    "description": "권한 없음",
    "content": {
        "application/json": {
            "example": {
                "header": {
                    "success": False,
                    "code": "FORBIDDEN",
                    "message": "접근 권한이 없습니다.",
                },
                "body": {"data": None},
            }
        }
    },
}
_ERR_404 = {
    "description": "게시글 없음",
    "content": {
        "application/json": {
            "example": {
                "header": {
                    "success": False,
                    "code": "POST_NOT_FOUND",
                    "message": "게시글을 찾을 수 없습니다.",
                },
                "body": {"data": None},
            }
        }
    },
}
_ERR_400 = {
    "description": "잘못된 요청",
    "content": {
        "application/json": {
            "examples": {
                "already_deleted": {
                    "summary": "이미 삭제된 게시글",
                    "value": {
                        "header": {
                            "success": False,
                            "code": "POST_ALREADY_DELETED",
                            "message": "이미 삭제된 게시글입니다.",
                        },
                        "body": {"data": None},
                    },
                },
                "not_deleted": {
                    "summary": "삭제되지 않은 게시글 복구",
                    "value": {
                        "header": {
                            "success": False,
                            "code": "POST_NOT_DELETED",
                            "message": "삭제된 게시글이 아닙니다.",
                        },
                        "body": {"data": None},
                    },
                },
            }
        }
    },
}


@admin_router.post(
    "/list",
    summary="게시글 전체 목록 조회 (관리자)",
    description="삭제 게시글 포함 여부와 게시판/작성자/공지 여부로 게시글을 조회합니다.",
    response_model=ApiResponse[PageData[AdminPostSummaryResponse]],
    status_code=status.HTTP_200_OK,
    responses={401: _ERR_401, 403: _ERR_403},
)
async def admin_list_posts(
    req: AdminPostListRequest,
    payload: dict[str, Any] = require_level(UserRole.ADMIN),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[PageData[AdminPostSummaryResponse]]:
    service = PostService(db)
    data = await service.admin_list_posts(req)
    return ApiResponse.success(data)


@admin_router.get(
    "/{post_id}",
    summary="게시글 단건 조회 (관리자)",
    description="삭제된 게시글도 조회합니다. 관리자 조회는 조회수를 증가시키지 않습니다.",
    response_model=ApiResponse[AdminPostDetailResponse],
    status_code=status.HTTP_200_OK,
    responses={401: _ERR_401, 403: _ERR_403, 404: _ERR_404},
)
async def admin_get_post(
    post_id: str,
    payload: dict[str, Any] = require_level(UserRole.ADMIN),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[AdminPostDetailResponse]:
    service = PostService(db)
    data = await service.admin_get_post(post_id)
    return ApiResponse.success(data)


@admin_router.delete(
    "/{post_id}",
    summary="게시글 논리 삭제 (관리자)",
    description="게시글을 논리 삭제합니다. 댓글과 첨부파일은 유지됩니다.",
    response_model=ApiResponse[None],
    status_code=status.HTTP_200_OK,
    responses={400: _ERR_400, 401: _ERR_401, 403: _ERR_403, 404: _ERR_404},
)
async def admin_delete_post(
    post_id: str,
    payload: dict[str, Any] = require_level(UserRole.ADMIN),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[None]:
    service = PostService(db)
    await service.admin_delete_post(post_id, payload)
    return ApiResponse.deleted("게시글이 삭제되었습니다.")


@admin_router.put(
    "/{post_id}/restore",
    summary="게시글 복구 (관리자)",
    description="논리 삭제된 게시글을 복구합니다.",
    response_model=ApiResponse[AdminPostDetailResponse],
    status_code=status.HTTP_200_OK,
    responses={400: _ERR_400, 401: _ERR_401, 403: _ERR_403, 404: _ERR_404},
)
async def admin_restore_post(
    post_id: str,
    payload: dict[str, Any] = require_level(UserRole.ADMIN),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[AdminPostDetailResponse]:
    service = PostService(db)
    data = await service.admin_restore_post(post_id, payload)
    return ApiResponse.updated(data, message="게시글이 복구되었습니다.")
