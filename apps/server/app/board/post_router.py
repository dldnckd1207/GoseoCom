"""게시글 라우터 — /api/v1/posts/ + /api/v1/boards/{board_code}/uploads"""

from typing import Any

from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.board.post_schemas import (
    PostCreateRequest,
    PostDetailResponse,
    PostListRequest,
    PostSummaryResponse,
    PostUpdateRequest,
)
from app.board.post_service import PostService
from app.core.common.decorators.require_level import require_level
from app.core.common.enums import UserRole
from app.core.common.response import ApiResponse, PageData
from app.core.files.schemas import FileUploadResponse
from app.db.session import get_db

post_router = APIRouter(prefix="/api/v1/posts", tags=["posts"])
board_upload_router = APIRouter(prefix="/api/v1/boards", tags=["posts"])

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
_ERR_404_POST = {
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
_ERR_404_BOARD = {
    "description": "게시판 없음",
    "content": {
        "application/json": {
            "example": {
                "header": {
                    "success": False,
                    "code": "BOARD_NOT_FOUND",
                    "message": "게시판을 찾을 수 없습니다.",
                },
                "body": {"data": None},
            }
        }
    },
}


@post_router.post(
    "/list",
    summary="게시글 목록 조회",
    description=(
        "게시판별 게시글 목록을 반환합니다.\n\n"
        "- `board_group` 있는 게시판(커뮤니티 등): 비회원도 목록 조회 가능 (`guest_read_yn` 무관)\n"
        "- `board_group` 없는 게시판: 비회원은 `guest_read_yn=true` 게시판만 조회 가능\n"
        "- 게시글 상세 조회(`GET /posts/{id}`)에서 `guest_read_yn` 권한을 별도 체크"
    ),
    response_model=ApiResponse[PageData[PostSummaryResponse]],
    status_code=status.HTTP_200_OK,
    responses={403: _ERR_403, 404: _ERR_404_BOARD},
)
async def list_posts(
    req: PostListRequest,
    payload: dict[str, Any] = require_level(UserRole.GUEST),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[PageData[PostSummaryResponse]]:
    service = PostService(db)
    data = await service.list_posts(req, payload)
    return ApiResponse.success(data)


@post_router.get(
    "/{post_id}",
    summary="게시글 단건 조회",
    description="게시글 전체 내용 + 첨부파일 목록을 반환합니다. 조회 시 view_count가 증가합니다.",
    response_model=ApiResponse[PostDetailResponse],
    status_code=status.HTTP_200_OK,
    responses={403: _ERR_403, 404: _ERR_404_POST},
)
async def get_post(
    post_id: str,
    payload: dict[str, Any] = require_level(UserRole.GUEST),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[PostDetailResponse]:
    service = PostService(db)
    data = await service.get_post(post_id, payload)
    return ApiResponse.success(data)


@post_router.post(
    "",
    summary="게시글 작성",
    description="게시판에 게시글을 작성합니다. `file_ids`는 선업로드 API로 발급된 ID 목록입니다.",
    response_model=ApiResponse[PostDetailResponse],
    status_code=status.HTTP_201_CREATED,
    responses={403: _ERR_403, 404: _ERR_404_BOARD},
)
async def create_post(
    req: PostCreateRequest,
    payload: dict[str, Any] = require_level(UserRole.USER),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[PostDetailResponse]:
    service = PostService(db)
    data = await service.create_post(req, payload)
    return ApiResponse.created(data, message="게시글이 작성되었습니다.")


@post_router.put(
    "/{post_id}",
    summary="게시글 수정",
    description="게시글을 수정합니다. 본인 또는 ADMIN만 가능합니다. `file_ids`는 최종 첨부 목록으로 교체됩니다.",
    response_model=ApiResponse[PostDetailResponse],
    status_code=status.HTTP_200_OK,
    responses={403: _ERR_403, 404: _ERR_404_POST},
)
async def update_post(
    post_id: str,
    req: PostUpdateRequest,
    payload: dict[str, Any] = require_level(UserRole.USER),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[PostDetailResponse]:
    service = PostService(db)
    data = await service.update_post(post_id, req, payload)
    return ApiResponse.updated(data, message="게시글이 수정되었습니다.")


@post_router.delete(
    "/{post_id}",
    summary="게시글 삭제",
    description="게시글을 논리 삭제합니다. 본인 또는 ADMIN만 가능합니다.",
    response_model=ApiResponse[None],
    status_code=status.HTTP_200_OK,
    responses={403: _ERR_403, 404: _ERR_404_POST},
)
async def delete_post(
    post_id: str,
    payload: dict[str, Any] = require_level(UserRole.USER),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[None]:
    service = PostService(db)
    await service.delete_post(post_id, payload)
    return ApiResponse.deleted("게시글이 삭제되었습니다.")


@board_upload_router.post(
    "/{board_code}/uploads",
    summary="게시판 파일 업로드",
    description="게시글 작성 전 파일을 선업로드합니다. 게시판 첨부 정책(`attach_yn`, `attach_ext`)을 검증합니다.",
    response_model=ApiResponse[FileUploadResponse],
    status_code=status.HTTP_201_CREATED,
    responses={403: _ERR_403, 404: _ERR_404_BOARD},
)
async def upload_file(
    board_code: str,
    file: UploadFile = File(...),
    payload: dict[str, Any] = require_level(UserRole.USER),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[FileUploadResponse]:
    service = PostService(db)
    data = await service.upload_file(board_code, file, payload)
    return ApiResponse.created(data, message="파일이 업로드되었습니다.")
