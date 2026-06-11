from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.common.decorators.require_level import require_level
from app.core.common.enums import UserRole
from app.core.common.response import ApiResponse, PageData
from app.db.session import get_db
from app.translate.schemas import (
    BookBookmarkResponse,
    BookDropdownItemResponse,
    BookFavoriteResponse,
    BookListItemResponse,
    BookListRequest,
    BookPublicListItemResponse,
    BookPublicListRequest,
    BookResponse,
    BookTitleUpdateRequest,
    OcrStartRequest,
    OcrStartResponse,
    PageEditRequest,
    PageEditResponse,
    TranslateStartRequest,
    TranslateStartResponse,
    TranslateTextRequest,
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
    "/ocr",
    summary="OCR 전용 시작",
    description="이미지를 OCR만 실행합니다. book_id로 폴링하여 OCR_COMPLETED 상태를 확인하세요.",
    response_model=ApiResponse[OcrStartResponse],
    status_code=status.HTTP_202_ACCEPTED,
)
async def start_ocr(
    req: OcrStartRequest,
    background_tasks: BackgroundTasks,
    payload: dict[str, Any] = require_level(UserRole.USER),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[OcrStartResponse]:
    service = TranslateService(db)
    data = await service.start_ocr(req.file_id, payload, background_tasks)
    return ApiResponse.success(data)


@router.post(
    "/text",
    summary="텍스트 번역",
    description="텍스트를 직접 입력하여 번역합니다. book_id가 있으면 OCR 완료된 Book을 이어서 번역합니다.",
    response_model=ApiResponse[TranslateStartResponse],
    status_code=status.HTTP_202_ACCEPTED,
)
async def translate_text(
    req: TranslateTextRequest,
    background_tasks: BackgroundTasks,
    payload: dict[str, Any] = require_level(UserRole.USER),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[TranslateStartResponse]:
    service = TranslateService(db)
    data = await service.translate_text(req, payload, background_tasks)
    return ApiResponse.success(data)


@router.put(
    "/{book_id}/favorite",
    summary="즐겨찾기 토글",
    description="번역 Book의 즐겨찾기 상태를 토글합니다. 본인 소유 Book만 가능합니다.",
    response_model=ApiResponse[BookFavoriteResponse],
    status_code=status.HTTP_200_OK,
)
async def toggle_favorite(
    book_id: str,
    payload: dict[str, Any] = require_level(UserRole.USER),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[BookFavoriteResponse]:
    service = TranslateService(db)
    data = await service.toggle_favorite(book_id, payload)
    return ApiResponse.success(data)


@router.put(
    "/{book_id}",
    summary="번역 제목 수정",
    description="번역 제목을 수정합니다. 본인 소유 Book만 수정 가능합니다.",
    response_model=ApiResponse[None],
    status_code=status.HTTP_200_OK,
)
async def update_book_title(
    book_id: str,
    req: BookTitleUpdateRequest,
    payload: dict[str, Any] = require_level(UserRole.USER),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[None]:
    service = TranslateService(db)
    await service.update_book_title(book_id, req.title, payload)
    return ApiResponse.success(None)


@router.put(
    "/{book_id}/pages/{page_no}",
    summary="번역 페이지 편집 저장",
    description="번역 결과를 편집하고 저장합니다. PageRevision 이력이 생성됩니다.",
    response_model=ApiResponse[PageEditResponse],
    status_code=status.HTTP_200_OK,
)
async def save_page_edit(
    book_id: str,
    page_no: int,
    req: PageEditRequest,
    payload: dict[str, Any] = require_level(UserRole.USER),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[PageEditResponse]:
    service = TranslateService(db)
    data = await service.save_page_edit(book_id, page_no, req, payload)
    return ApiResponse.success(data)


@router.get(
    "/mine",
    summary="내 완료 번역 목록 (드롭다운용)",
    response_model=ApiResponse[list[BookDropdownItemResponse]],
    status_code=status.HTTP_200_OK,
)
async def list_my_completed_books(
    payload: dict[str, Any] = require_level(UserRole.USER),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[list[BookDropdownItemResponse]]:
    service = TranslateService(db)
    data = await service.list_my_completed_books(payload["sub"])
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
    "/public/list",
    summary="공개 번역 목록",
    description="완료된 전체 사용자의 번역 결과를 반환합니다. 비로그인 허용, 로그인 시 is_bookmarked 포함.",
    response_model=ApiResponse[PageData[BookPublicListItemResponse]],
    status_code=status.HTTP_200_OK,
)
async def list_public_books(
    req: BookPublicListRequest,
    payload: dict[str, Any] = require_level(UserRole.GUEST),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[PageData[BookPublicListItemResponse]]:
    user_id: str | None = payload.get("sub") or None
    service = TranslateService(db)
    data = await service.list_public_books(req, user_id)
    return ApiResponse.success(data)


@router.put(
    "/public/{book_id}/bookmark",
    summary="공개 번역 북마크 토글",
    description="공개 번역 결과를 북마크합니다. 본인 Book은 불가. 로그인 필수.",
    response_model=ApiResponse[BookBookmarkResponse],
    status_code=status.HTTP_200_OK,
)
async def toggle_bookmark(
    book_id: str,
    payload: dict[str, Any] = require_level(UserRole.USER),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[BookBookmarkResponse]:
    service = TranslateService(db)
    data = await service.toggle_bookmark(book_id, payload)
    return ApiResponse.success(data)


@router.get(
    "/public/{book_id}",
    summary="공개 번역 상세",
    description="완료된 번역 결과를 공개 조회합니다. 인증 불필요.",
    response_model=ApiResponse[BookResponse],
    status_code=status.HTTP_200_OK,
)
async def get_public_book(
    book_id: str,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[BookResponse]:
    service = TranslateService(db)
    data = await service.get_public_book(book_id)
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
