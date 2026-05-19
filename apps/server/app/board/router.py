"""게시판 클라이언트 라우터 — /api/v1/boards/"""

from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.board.schemas import (
    BoardCategoryResponse,
    BoardDetailResponse,
    BoardListRequest,
    BoardSummaryResponse,
)
from app.board.service import BoardService
from app.core.common.decorators.require_level import require_level
from app.core.common.enums import UserRole
from app.core.common.response import ApiResponse, PageData
from app.db.session import get_db

router = APIRouter(prefix="/api/v1/boards", tags=["boards"])

_ERR_403_FORBIDDEN = {
    "description": "권한 없음",
    "content": {
        "application/json": {
            "examples": {
                "guest_restricted": {
                    "summary": "비회원 접근 불가 게시판",
                    "value": {
                        "header": {
                            "success": False,
                            "code": "FORBIDDEN",
                            "message": "접근 권한이 없습니다.",
                        },
                        "body": {"data": None},
                    },
                }
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


@router.post(
    "/list",
    summary="게시판 목록 조회",
    description=(
        "활성화된 게시판 목록을 반환합니다.\n\n"
        "**`board_group` 미지정 시 (기본 동작)**\n"
        "- 비회원: `guest_read_yn=true` 게시판만 반환\n"
        "- 로그인 사용자: `read_yn=true` 게시판만 반환\n\n"
        "**`board_group` 지정 시**\n"
        "- 해당 그룹의 모든 게시판을 반환 (`guest_read_yn` / `read_yn` 무관)\n"
        "- 게시글 열람 권한(`guest_read_yn`)은 게시글 상세 API에서 별도 체크"
    ),
    response_model=ApiResponse[PageData[BoardSummaryResponse]],
    status_code=status.HTTP_200_OK,
)
async def list_boards(
    req: BoardListRequest,
    payload: dict[str, Any] = require_level(UserRole.GUEST),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[PageData[BoardSummaryResponse]]:
    service = BoardService(db)
    data = await service.list_boards(req, payload)
    return ApiResponse.success(data)


@router.get(
    "/{board_code}/categories",
    summary="게시판 카테고리 목록",
    description="게시판의 활성 카테고리 목록을 반환합니다. 인증 불필요.",
    response_model=ApiResponse[list[BoardCategoryResponse]],
    status_code=status.HTTP_200_OK,
)
async def list_board_categories(
    board_code: str,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[list[BoardCategoryResponse]]:
    service = BoardService(db)
    data = await service.list_categories(board_code)
    return ApiResponse.success(data)


@router.get(
    "/{board_code}",
    summary="게시판 단건 조회",
    description=(
        "`board_code`(slug)로 게시판 전체 설정을 반환합니다.\n\n"
        "비회원이 `guest_read_yn=false` 게시판에 접근하면 403을 반환합니다."
    ),
    response_model=ApiResponse[BoardDetailResponse],
    status_code=status.HTTP_200_OK,
    responses={
        403: _ERR_403_FORBIDDEN,
        404: _ERR_404_BOARD,
    },
)
async def get_board(
    board_code: str,
    payload: dict[str, Any] = require_level(UserRole.GUEST),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[BoardDetailResponse]:
    service = BoardService(db)
    data = await service.get_board_by_code(board_code, payload)
    return ApiResponse.success(data)
