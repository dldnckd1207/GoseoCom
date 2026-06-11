"""번역 이력 관리자 라우터 — /admin/api/v1/translations/"""

from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.common.decorators.require_level import require_level
from app.core.common.enums import UserRole
from app.core.common.response import ApiResponse, PageData
from app.db.session import get_db
from app.translate.schemas import (
    AdminTranslationDetailResponse,
    AdminTranslationListRequest,
    AdminTranslationSummaryResponse,
    TranslateStartResponse,
)
from app.translate.service import TranslateService

admin_router = APIRouter(prefix="/admin/api/v1/translations", tags=["admin-translations"])

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
    "description": "번역 이력 없음",
    "content": {
        "application/json": {
            "example": {
                "header": {
                    "success": False,
                    "code": "BOOK_NOT_FOUND",
                    "message": "번역 이력을 찾을 수 없습니다.",
                },
                "body": {"data": None},
            }
        }
    },
}
_ERR_409 = {
    "description": "재시도 불가",
    "content": {
        "application/json": {
            "examples": {
                "not_failed": {
                    "summary": "실패 상태 아님",
                    "value": {
                        "header": {
                            "success": False,
                            "code": "BOOK_NOT_FAILED",
                            "message": "실패 상태의 번역만 재시도할 수 있습니다.",
                        },
                        "body": {"data": None},
                    },
                },
                "source_file_missing": {
                    "summary": "원본 파일 없음",
                    "value": {
                        "header": {
                            "success": False,
                            "code": "BOOK_SOURCE_FILE_MISSING",
                            "message": "원본 파일이 없어 재시도할 수 없습니다.",
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
    summary="번역 이력 전체 목록 조회 (관리자)",
    description="전체 사용자의 번역 이력을 상태와 키워드로 조회합니다.",
    response_model=ApiResponse[PageData[AdminTranslationSummaryResponse]],
    status_code=status.HTTP_200_OK,
    responses={401: _ERR_401, 403: _ERR_403},
)
async def admin_list_translations(
    req: AdminTranslationListRequest,
    payload: dict[str, Any] = require_level(UserRole.ADMIN),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[PageData[AdminTranslationSummaryResponse]]:
    service = TranslateService(db)
    data = await service.admin_list_translations(req, payload["sub"])
    return ApiResponse.success(data)


@admin_router.get(
    "/{book_id}",
    summary="번역 이력 단건 조회 (관리자)",
    description="소유자 제한 없이 번역 상세, 페이지별 상태, 최근 실행 이력을 조회합니다.",
    response_model=ApiResponse[AdminTranslationDetailResponse],
    status_code=status.HTTP_200_OK,
    responses={401: _ERR_401, 403: _ERR_403, 404: _ERR_404},
)
async def admin_get_translation(
    book_id: str,
    payload: dict[str, Any] = require_level(UserRole.ADMIN),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[AdminTranslationDetailResponse]:
    service = TranslateService(db)
    data = await service.admin_get_translation(book_id, payload["sub"])
    return ApiResponse.success(data)


@admin_router.put(
    "/{book_id}/retry",
    summary="번역 재시도 (관리자)",
    description="실패한 번역을 소유자 제한 없이 관리자 권한으로 재시도합니다.",
    response_model=ApiResponse[TranslateStartResponse],
    status_code=status.HTTP_202_ACCEPTED,
    responses={401: _ERR_401, 403: _ERR_403, 404: _ERR_404, 409: _ERR_409},
)
async def admin_retry_translation(
    book_id: str,
    background_tasks: BackgroundTasks,
    payload: dict[str, Any] = require_level(UserRole.ADMIN),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[TranslateStartResponse]:
    service = TranslateService(db)
    data = await service.admin_retry_translate(book_id, payload, background_tasks)
    return ApiResponse.success(data)
