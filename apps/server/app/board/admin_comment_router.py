"""댓글 관리자 라우터 — /admin/api/v1/comments/"""

from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.board.comment_schemas import (
    AdminCommentListRequest,
    AdminCommentResponse,
)
from app.board.comment_service import CommentService
from app.core.common.decorators.require_level import require_level
from app.core.common.enums import UserRole
from app.core.common.response import ApiResponse, PageData
from app.db.session import get_db

admin_comment_router = APIRouter(prefix="/admin/api/v1/comments", tags=["admin-comments"])

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
    "description": "댓글 없음",
    "content": {
        "application/json": {
            "example": {
                "header": {
                    "success": False,
                    "code": "COMMENT_NOT_FOUND",
                    "message": "필터링된 댓글을 찾을 수 없습니다.",
                },
                "body": {"data": None},
            }
        }
    },
}


@admin_comment_router.post(
    "/list",
    summary="필터링된 댓글 목록 조회 (관리자)",
    description="AI가 악성으로 표시한 댓글 목록을 반환합니다. keyword로 내용/작성자 검색 가능.",
    response_model=ApiResponse[PageData[AdminCommentResponse]],
    status_code=status.HTTP_200_OK,
    responses={401: _ERR_401, 403: _ERR_403},
)
async def admin_list_filtered_comments(
    req: AdminCommentListRequest,
    payload: dict[str, Any] = require_level(UserRole.ADMIN),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[PageData[AdminCommentResponse]]:
    service = CommentService(db)
    data = await service.admin_list_flagged(req)
    return ApiResponse.success(data)


@admin_comment_router.put(
    "/{comment_id}/approve",
    summary="필터링된 댓글 승인 (관리자)",
    description="AI가 필터링한 댓글을 정상으로 승인합니다. is_filtered=False, filter_status=CLEAN으로 전환됩니다.",
    response_model=ApiResponse[AdminCommentResponse],
    status_code=status.HTTP_200_OK,
    responses={401: _ERR_401, 403: _ERR_403, 404: _ERR_404},
)
async def admin_approve_comment(
    comment_id: str,
    payload: dict[str, Any] = require_level(UserRole.ADMIN),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[AdminCommentResponse]:
    service = CommentService(db)
    data = await service.admin_approve_comment(comment_id, reviewer_id=payload["sub"])
    return ApiResponse.updated(data, message="댓글이 승인되었습니다.")


@admin_comment_router.delete(
    "/{comment_id}",
    summary="필터링된 댓글 거부/삭제 (관리자)",
    description="AI가 필터링한 댓글을 거부하여 소프트 삭제합니다.",
    response_model=ApiResponse[None],
    status_code=status.HTTP_200_OK,
    responses={401: _ERR_401, 403: _ERR_403, 404: _ERR_404},
)
async def admin_reject_comment(
    comment_id: str,
    payload: dict[str, Any] = require_level(UserRole.ADMIN),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[None]:
    service = CommentService(db)
    await service.admin_reject_comment(comment_id, reviewer_id=payload["sub"])
    return ApiResponse.deleted("댓글이 삭제되었습니다.")
