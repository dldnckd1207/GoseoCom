"""댓글 라우터 — /api/v1/posts/{post_id}/comments/"""

from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.board.comment_schemas import (
    CommentCreateRequest,
    CommentListRequest,
    CommentResponse,
    CommentUpdateRequest,
)
from app.board.comment_service import CommentService
from app.core.common.decorators.require_level import require_level
from app.core.common.enums import UserRole
from app.core.common.response import ApiResponse, PageData
from app.db.session import get_db

comment_router = APIRouter(
    prefix="/api/v1/posts/{post_id}/comments",
    tags=["comments"],
)

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
_ERR_404_COMMENT = {
    "description": "댓글 없음",
    "content": {
        "application/json": {
            "example": {
                "header": {
                    "success": False,
                    "code": "COMMENT_NOT_FOUND",
                    "message": "댓글을 찾을 수 없습니다.",
                },
                "body": {"data": None},
            }
        }
    },
}


@comment_router.post(
    "/list",
    summary="댓글 목록 조회",
    description=(
        "Nested 구조로 댓글 목록을 반환합니다. `total`은 root 댓글 수 기준입니다.\n\n"
        "삭제된 root 댓글은 placeholder(`is_deleted=true`)로 포함됩니다."
    ),
    response_model=ApiResponse[PageData[CommentResponse]],
    status_code=status.HTTP_200_OK,
    responses={403: _ERR_403},
)
async def list_comments(
    post_id: str,
    req: CommentListRequest,
    payload: dict[str, Any] = require_level(UserRole.GUEST),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[PageData[CommentResponse]]:
    service = CommentService(db)
    data = await service.list_comments(post_id, req, payload)
    return ApiResponse.success(data)


@comment_router.post(
    "",
    summary="댓글 작성",
    description="게시글에 댓글을 작성합니다. `parent_id` 지정 시 대댓글(depth=1)입니다.",
    response_model=ApiResponse[CommentResponse],
    status_code=status.HTTP_201_CREATED,
    responses={403: _ERR_403},
)
async def create_comment(
    post_id: str,
    req: CommentCreateRequest,
    payload: dict[str, Any] = require_level(UserRole.USER),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[CommentResponse]:
    service = CommentService(db)
    data = await service.create_comment(post_id, req, payload)
    return ApiResponse.created(data, message="댓글이 작성되었습니다.")


@comment_router.put(
    "/{comment_id}",
    summary="댓글 수정",
    description="댓글을 수정합니다. 본인 또는 ADMIN만 가능합니다.",
    response_model=ApiResponse[CommentResponse],
    status_code=status.HTTP_200_OK,
    responses={403: _ERR_403, 404: _ERR_404_COMMENT},
)
async def update_comment(
    post_id: str,
    comment_id: str,
    req: CommentUpdateRequest,
    payload: dict[str, Any] = require_level(UserRole.USER),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[CommentResponse]:
    service = CommentService(db)
    data = await service.update_comment(post_id, comment_id, req, payload)
    return ApiResponse.updated(data, message="댓글이 수정되었습니다.")


@comment_router.delete(
    "/{comment_id}",
    summary="댓글 삭제",
    description=(
        "댓글을 논리 삭제합니다. 본인 또는 ADMIN만 가능합니다.\n\n"
        "삭제 후 댓글 목록에서 placeholder(`삭제된 댓글입니다.`)로 표시됩니다."
    ),
    response_model=ApiResponse[None],
    status_code=status.HTTP_200_OK,
    responses={403: _ERR_403, 404: _ERR_404_COMMENT},
)
async def delete_comment(
    post_id: str,
    comment_id: str,
    payload: dict[str, Any] = require_level(UserRole.USER),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[None]:
    service = CommentService(db)
    await service.delete_comment(post_id, comment_id, payload)
    return ApiResponse.deleted("댓글이 삭제되었습니다.")
