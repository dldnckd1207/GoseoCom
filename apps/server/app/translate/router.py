from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.common.decorators.require_level import require_level
from app.core.common.enums import UserRole
from app.core.common.response import ApiResponse, PageData
from app.db.session import get_db
from app.translate.schemas import (
    BookListItemResponse,
    BookListRequest,
    BookResponse,
    TranslateStartRequest,
    TranslateStartResponse,
)
from app.translate.service import TranslateService

router = APIRouter(prefix="/api/v1/translate", tags=["translate"])


@router.post(
    "",
    summary="고서 번역 시작",
    description=(
        "업로드된 이미지의 file_id로 번역을 시작합니다.\n\n"
        "이미지는 먼저 `POST /api/v1/uploads`로 업로드한 뒤 반환된 `file_id`를 사용하세요.\n\n"
        "OCR → 번역 파이프라인이 백그라운드로 실행되며, book_id로 결과를 폴링할 수 있습니다."
    ),
    response_model=ApiResponse[TranslateStartResponse],
    status_code=status.HTTP_202_ACCEPTED,
)
async def start_translate(
    req: TranslateStartRequest,
    background_tasks: BackgroundTasks,
    payload: dict[str, Any] = require_level(UserRole.USER),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[TranslateStartResponse]:
    service = TranslateService(db)
    data = await service.start_translate(req.file_id, payload, background_tasks)
    return ApiResponse.success(data)


@router.post(
    "/list",
    summary="내 번역 목록",
    response_model=ApiResponse[PageData[BookListItemResponse]],
    status_code=status.HTTP_200_OK,
)
async def list_books(
    req: BookListRequest,
    payload: dict[str, Any] = require_level(UserRole.USER),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[PageData[BookListItemResponse]]:
    service = TranslateService(db)
    data = await service.list_books(req, payload)
    return ApiResponse.success(data)


@router.post(
    "/{book_id}/retry",
    summary="번역 재시도",
    description="FAILED 상태의 book을 원본 파일로 다시 번역합니다.",
    response_model=ApiResponse[TranslateStartResponse],
    status_code=status.HTTP_202_ACCEPTED,
)
async def retry_translate(
    book_id: str,
    background_tasks: BackgroundTasks,
    payload: dict[str, Any] = require_level(UserRole.USER),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[TranslateStartResponse]:
    service = TranslateService(db)
    data = await service.retry_translate(book_id, payload, background_tasks)
    return ApiResponse.success(data)


@router.get(
    "/{book_id}",
    summary="번역 결과 조회",
    description="book_id로 번역 상태 및 결과를 조회합니다. 본인 소유 Book만 조회 가능합니다.",
    response_model=ApiResponse[BookResponse],
    status_code=status.HTTP_200_OK,
)
async def get_book(
    book_id: str,
    payload: dict[str, Any] = require_level(UserRole.USER),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[BookResponse]:
    service = TranslateService(db)
    data = await service.get_book(book_id, payload)
    return ApiResponse.success(data)
