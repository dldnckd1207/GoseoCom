"""게시판 관리자 라우터 — /admin/api/v1/boards/"""

from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.board.schemas import (
    AdminBoardCategoryCreateRequest,
    AdminBoardCategoryResponse,
    AdminBoardCategoryUpdateRequest,
    AdminBoardCreateRequest,
    AdminBoardListRequest,
    AdminBoardResponse,
    AdminBoardUpdateRequest,
)
from app.board.service import BoardService
from app.core.common.decorators.require_level import require_level
from app.core.common.enums import UserRole
from app.core.common.response import ApiResponse, PageData
from app.db.session import get_db

admin_router = APIRouter(prefix="/admin/api/v1/boards", tags=["admin-boards"])

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

_ERR_409_CONFLICT = {
    "description": "충돌",
    "content": {
        "application/json": {
            "examples": {
                "code_exists": {
                    "summary": "board_code 중복",
                    "value": {
                        "header": {
                            "success": False,
                            "code": "BOARD_CODE_ALREADY_EXISTS",
                            "message": "이미 사용 중인 게시판 코드입니다.",
                        },
                        "body": {"data": None},
                    },
                },
                "has_posts": {
                    "summary": "게시글 있는 게시판 삭제 시도",
                    "value": {
                        "header": {
                            "success": False,
                            "code": "BOARD_HAS_POSTS",
                            "message": "게시글이 있는 게시판은 삭제할 수 없습니다.",
                        },
                        "body": {"data": None},
                    },
                },
            }
        }
    },
}

_ERR_404_CATEGORY = {
    "description": "카테고리 없음",
    "content": {
        "application/json": {
            "example": {
                "header": {
                    "success": False,
                    "code": "CATEGORY_NOT_FOUND",
                    "message": "카테고리를 찾을 수 없습니다.",
                },
                "body": {"data": None},
            }
        }
    },
}


@admin_router.post(
    "/list",
    summary="게시판 전체 목록 조회 (관리자)",
    description="비활성 게시판 포함 전체 목록을 반환합니다. `keyword`, `use_yn`으로 필터링 가능합니다.",
    response_model=ApiResponse[PageData[AdminBoardResponse]],
    status_code=status.HTTP_200_OK,
    responses={401: _ERR_401_UNAUTHORIZED, 403: _ERR_403_FORBIDDEN},
)
async def admin_list_boards(
    req: AdminBoardListRequest,
    payload: dict[str, Any] = require_level(UserRole.ADMIN),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[PageData[AdminBoardResponse]]:
    service = BoardService(db)
    data = await service.admin_list_boards(req)
    return ApiResponse.success(data)


@admin_router.get(
    "/{board_id}",
    summary="게시판 단건 조회 (관리자)",
    response_model=ApiResponse[AdminBoardResponse],
    status_code=status.HTTP_200_OK,
    responses={401: _ERR_401_UNAUTHORIZED, 403: _ERR_403_FORBIDDEN, 404: _ERR_404_BOARD},
)
async def admin_get_board(
    board_id: str,
    payload: dict[str, Any] = require_level(UserRole.ADMIN),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[AdminBoardResponse]:
    service = BoardService(db)
    data = await service.admin_get_board(board_id)
    return ApiResponse.success(data)


@admin_router.post(
    "",
    summary="게시판 생성 (관리자)",
    response_model=ApiResponse[AdminBoardResponse],
    status_code=status.HTTP_201_CREATED,
    responses={401: _ERR_401_UNAUTHORIZED, 403: _ERR_403_FORBIDDEN, 409: _ERR_409_CONFLICT},
)
async def admin_create_board(
    req: AdminBoardCreateRequest,
    payload: dict[str, Any] = require_level(UserRole.ADMIN),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[AdminBoardResponse]:
    service = BoardService(db)
    data = await service.admin_create_board(req, user_id=payload["sub"])
    return ApiResponse.created(data, message="게시판이 생성되었습니다.")


@admin_router.put(
    "/{board_id}",
    summary="게시판 수정 (관리자)",
    response_model=ApiResponse[AdminBoardResponse],
    status_code=status.HTTP_200_OK,
    responses={
        401: _ERR_401_UNAUTHORIZED,
        403: _ERR_403_FORBIDDEN,
        404: _ERR_404_BOARD,
        409: _ERR_409_CONFLICT,
    },
)
async def admin_update_board(
    board_id: str,
    req: AdminBoardUpdateRequest,
    payload: dict[str, Any] = require_level(UserRole.ADMIN),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[AdminBoardResponse]:
    service = BoardService(db)
    data = await service.admin_update_board(board_id, req, user_id=payload["sub"])
    return ApiResponse.updated(data, message="게시판이 수정되었습니다.")


@admin_router.delete(
    "/{board_id}",
    summary="게시판 삭제 (관리자)",
    description=(
        "게시판을 논리 삭제(`del_yn=true`)합니다.\n\n"
        "해당 게시판의 게시글, 댓글, 카테고리도 함께 논리 삭제됩니다."
    ),
    response_model=ApiResponse[None],
    status_code=status.HTTP_200_OK,
    responses={
        401: _ERR_401_UNAUTHORIZED,
        403: _ERR_403_FORBIDDEN,
        404: _ERR_404_BOARD,
        409: _ERR_409_CONFLICT,
    },
)
async def admin_delete_board(
    board_id: str,
    payload: dict[str, Any] = require_level(UserRole.ADMIN),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[None]:
    service = BoardService(db)
    await service.admin_delete_board(board_id, user_id=payload["sub"])
    return ApiResponse.deleted("게시판이 삭제되었습니다.")


@admin_router.get(
    "/{board_id}/categories",
    summary="게시판 카테고리 목록 조회 (관리자)",
    response_model=ApiResponse[list[AdminBoardCategoryResponse]],
    status_code=status.HTTP_200_OK,
    responses={401: _ERR_401_UNAUTHORIZED, 403: _ERR_403_FORBIDDEN, 404: _ERR_404_BOARD},
)
async def admin_list_board_categories(
    board_id: str,
    payload: dict[str, Any] = require_level(UserRole.ADMIN),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[list[AdminBoardCategoryResponse]]:
    service = BoardService(db)
    data = await service.admin_list_categories(board_id)
    return ApiResponse.success(data)


@admin_router.post(
    "/{board_id}/categories",
    summary="게시판 카테고리 생성 (관리자)",
    response_model=ApiResponse[AdminBoardCategoryResponse],
    status_code=status.HTTP_201_CREATED,
    responses={401: _ERR_401_UNAUTHORIZED, 403: _ERR_403_FORBIDDEN, 404: _ERR_404_BOARD},
)
async def admin_create_board_category(
    board_id: str,
    req: AdminBoardCategoryCreateRequest,
    payload: dict[str, Any] = require_level(UserRole.ADMIN),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[AdminBoardCategoryResponse]:
    service = BoardService(db)
    data = await service.admin_create_category(board_id, req, user_id=payload["sub"])
    return ApiResponse.created(data, message="카테고리가 생성되었습니다.")


@admin_router.put(
    "/{board_id}/categories/{category_id}",
    summary="게시판 카테고리 수정 (관리자)",
    response_model=ApiResponse[AdminBoardCategoryResponse],
    status_code=status.HTTP_200_OK,
    responses={
        401: _ERR_401_UNAUTHORIZED,
        403: _ERR_403_FORBIDDEN,
        404: _ERR_404_CATEGORY,
    },
)
async def admin_update_board_category(
    board_id: str,
    category_id: str,
    req: AdminBoardCategoryUpdateRequest,
    payload: dict[str, Any] = require_level(UserRole.ADMIN),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[AdminBoardCategoryResponse]:
    service = BoardService(db)
    data = await service.admin_update_category(board_id, category_id, req, user_id=payload["sub"])
    return ApiResponse.updated(data, message="카테고리가 수정되었습니다.")


@admin_router.delete(
    "/{board_id}/categories/{category_id}",
    summary="게시판 카테고리 삭제 (관리자)",
    description="게시판 카테고리를 논리 삭제(`del_yn=true`)합니다.",
    response_model=ApiResponse[None],
    status_code=status.HTTP_200_OK,
    responses={
        401: _ERR_401_UNAUTHORIZED,
        403: _ERR_403_FORBIDDEN,
        404: _ERR_404_CATEGORY,
    },
)
async def admin_delete_board_category(
    board_id: str,
    category_id: str,
    payload: dict[str, Any] = require_level(UserRole.ADMIN),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[None]:
    service = BoardService(db)
    await service.admin_delete_category(board_id, category_id, user_id=payload["sub"])
    return ApiResponse.deleted("카테고리가 삭제되었습니다.")
