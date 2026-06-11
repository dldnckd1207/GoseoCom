from datetime import UTC, date, datetime
from typing import Any

from fastapi import BackgroundTasks, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.common.id_generator import next_id
from app.core.common.response import PageData
from app.core.files.repository import FileRepository
from app.translate.models import Book, BookPage, PageRevision, PipelineRun
from app.translate.pipeline.runner import run_ocr_only, run_pipeline, run_translate_only
from app.translate.repository import (
    BookBookmarkRepository,
    BookPageRepository,
    BookRepository,
    PageRevisionRepository,
    PipelineRunRepository,
)
from app.translate.schemas import (
    AdminPipelineRunResponse,
    AdminTranslationDetailResponse,
    AdminTranslationListRequest,
    AdminTranslationPageResponse,
    AdminTranslationSummaryResponse,
    BookBookmarkResponse,
    BookDropdownItemResponse,
    BookFavoriteResponse,
    BookListItemResponse,
    BookListRequest,
    BookPublicListItemResponse,
    BookPublicListRequest,
    BookResponse,
    OcrStartResponse,
    PageEditRequest,
    PageEditResponse,
    TranslateStartResponse,
    TranslateTextRequest,
)

_MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB


async def _validate_image_file(file_repo: FileRepository, file_id: str, user_id: str) -> Any:
    file_entity = await file_repo.get_by_id(file_id)
    if not file_entity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "FILE_NOT_FOUND", "message": "파일을 찾을 수 없습니다."},
        )
    if file_entity.created_by != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FILE_ACCESS_FORBIDDEN", "message": "접근 권한이 없습니다."},
        )
    if not file_entity.mime_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_IMAGE_TYPE", "message": "이미지 파일만 번역 가능합니다."},
        )
    if file_entity.file_size > _MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "IMAGE_SIZE_EXCEEDED",
                "message": "이미지 크기는 10MB를 초과할 수 없습니다.",
            },
        )
    return file_entity


async def _check_daily_limit(book_repo: BookRepository, user_id: str) -> None:
    limit = settings.translate_daily_limit
    if limit <= 0:
        return
    count = await book_repo.count_today_by_owner(user_id, date.today())
    if count >= limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "code": "DAILY_LIMIT_EXCEEDED",
                "message": f"오늘 번역 가능한 횟수({limit}건)를 초과했습니다. 내일 다시 시도해주세요.",
            },
        )


def _build_book_response(book: Book) -> BookResponse:
    source_file_url = book.source_file.url_path if book.source_file else None
    data = BookResponse.model_validate(book)
    data.source_file_url = source_file_url
    return data


def _can_retry_book(book: Book) -> bool:
    return bool(
        book.status == "FAILED"
        and book.source_file_id is not None
        and book.source_file is not None
        and book.source_file.local_path
    )


def _retry_disabled_reason(book: Book) -> str | None:
    if book.status != "FAILED":
        return "실패 상태의 번역만 재시도할 수 있습니다."
    if not book.source_file_id or not book.source_file or not book.source_file.local_path:
        return "원본 파일이 없어 재시도할 수 없습니다."
    return None


def _build_admin_page_response(page: BookPage) -> AdminTranslationPageResponse:
    return AdminTranslationPageResponse(
        page_no=page.page_no,
        status=page.status,
        ocr_text=page.ocr_text,
        literal_text=page.literal_text,
        interpretive_text=page.interpretive_text,
        has_ocr_text=bool(page.ocr_text),
        has_literal_text=bool(page.literal_text),
        has_interpretive_text=bool(page.interpretive_text),
        ocr_engine=page.ocr_engine,
        translator_engine=page.translator_engine,
    )


def _build_admin_run_response(run: PipelineRun) -> AdminPipelineRunResponse:
    return AdminPipelineRunResponse(
        id=run.id,
        trigger_type=run.trigger_type,
        status=run.status,
        started_at=run.started_at,
        completed_at=run.completed_at,
        duration_ms=run.duration_ms,
        error_msg=run.error_msg,
    )


class TranslateService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.book_repo = BookRepository(db)
        self.page_repo = BookPageRepository(db)
        self.run_repo = PipelineRunRepository(db)
        self.revision_repo = PageRevisionRepository(db)
        self.bookmark_repo = BookBookmarkRepository(db)
        self.file_repo = FileRepository(db)

    async def start_translate(
        self,
        file_id: str,
        payload: dict[str, Any],
        background_tasks: BackgroundTasks,
    ) -> TranslateStartResponse:
        user_id: str = payload["sub"]
        await _check_daily_limit(self.book_repo, user_id)

        file_entity = await _validate_image_file(self.file_repo, file_id, user_id)

        now = datetime.now(UTC)

        book = Book(
            id=await next_id("BOOK_", self.db),
            owner_user_id=user_id,
            source_file_id=file_entity.id,
            title=file_entity.original_name,
            book_type="QUICK",
            source_type="IMAGE",
            total_pages=1,
            status="PENDING",
            created_at=now,
            created_by=user_id,
            updated_at=now,
            updated_by=user_id,
        )
        await self.book_repo.create(book)

        page = BookPage(
            id=await next_id("BPAGE_", self.db),
            book_id=book.id,
            page_no=1,
            status="PENDING",
            created_at=now,
            created_by=user_id,
            updated_at=now,
            updated_by=user_id,
        )
        await self.page_repo.create(page)

        pipeline_run = PipelineRun(
            trigger_type="TRANSLATOR",
            triggered_by=user_id,
            book_id=book.id,
            status="PENDING",
            created_at=now,
        )
        await self.run_repo.create(pipeline_run)

        await self.db.commit()

        background_tasks.add_task(run_pipeline, book.id, file_entity.local_path, pipeline_run.id)

        return TranslateStartResponse(book_id=book.id, status=book.status)

    async def admin_list_translations(
        self,
        req: AdminTranslationListRequest,
        current_user_id: str,
    ) -> PageData[AdminTranslationSummaryResponse]:
        keyword = req.keyword.strip() if req.keyword else None
        books, total = await self.book_repo.admin_list(
            page=req.page,
            size=req.size,
            keyword=keyword or None,
            status=req.status,
        )
        latest_runs = await self.run_repo.get_latest_by_book_ids([book.id for book in books])

        items = []
        for book in books:
            latest_run = latest_runs.get(book.id)
            items.append(
                AdminTranslationSummaryResponse(
                    book_id=book.id,
                    title=book.title,
                    owner_name=book.owner.name if book.owner else "",
                    owner_is_self=book.owner_user_id == current_user_id,
                    status=book.status,
                    total_pages=book.total_pages,
                    created_at=book.created_at,
                    latest_run_status=latest_run.status if latest_run else None,
                    latest_run_error_msg=latest_run.error_msg if latest_run else None,
                    can_retry=_can_retry_book(book),
                )
            )

        return PageData(items=items, total=total, page=req.page, size=req.size)

    async def admin_get_translation(
        self,
        book_id: str,
        current_user_id: str,
    ) -> AdminTranslationDetailResponse:
        book = await self.book_repo.admin_get_detail(book_id)
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "BOOK_NOT_FOUND", "message": "번역 이력을 찾을 수 없습니다."},
            )
        runs = await self.run_repo.list_by_book(book_id, limit=10)
        pages = sorted(book.pages, key=lambda page: page.page_no)
        return AdminTranslationDetailResponse(
            book_id=book.id,
            title=book.title,
            owner_name=book.owner.name if book.owner else "",
            owner_is_self=book.owner_user_id == current_user_id,
            status=book.status,
            book_type=book.book_type,
            source_type=book.source_type,
            total_pages=book.total_pages,
            source_file_url=book.source_file.url_path if book.source_file else None,
            created_at=book.created_at,
            updated_at=book.updated_at,
            can_retry=_can_retry_book(book),
            retry_disabled_reason=_retry_disabled_reason(book),
            pages=[_build_admin_page_response(page) for page in pages],
            pipeline_runs=[_build_admin_run_response(run) for run in runs],
        )

    async def admin_retry_translate(
        self,
        book_id: str,
        payload: dict[str, Any],
        background_tasks: BackgroundTasks,
    ) -> TranslateStartResponse:
        admin_id: str = payload["sub"]
        book = await self.book_repo.admin_get_detail(book_id)
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "BOOK_NOT_FOUND", "message": "번역 이력을 찾을 수 없습니다."},
            )
        if book.status != "FAILED":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "BOOK_NOT_FAILED",
                    "message": "실패 상태의 번역만 재시도할 수 있습니다.",
                },
            )
        if not book.source_file or not book.source_file.local_path:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "BOOK_SOURCE_FILE_MISSING",
                    "message": "원본 파일이 없어 재시도할 수 없습니다.",
                },
            )

        now = datetime.now(UTC)
        book.status = "PENDING"
        book.updated_at = now
        book.updated_by = admin_id

        for page in book.pages:
            page.status = "PENDING"
            page.ocr_text = None
            page.literal_text = None
            page.interpretive_text = None
            page.updated_at = now
            page.updated_by = admin_id

        pipeline_run = PipelineRun(
            trigger_type="TRANSLATOR",
            triggered_by=admin_id,
            book_id=book.id,
            status="PENDING",
            created_at=now,
        )
        await self.run_repo.create(pipeline_run)
        source_path = book.source_file.local_path
        await self.db.commit()

        background_tasks.add_task(run_pipeline, book.id, source_path, pipeline_run.id)

        return TranslateStartResponse(book_id=book.id, status=book.status)

    async def retry_translate(
        self,
        book_id: str,
        payload: dict[str, Any],
        background_tasks: BackgroundTasks,
    ) -> TranslateStartResponse:
        user_id: str = payload["sub"]

        book = await self.book_repo.get_by_id_with_source_file(book_id)
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "BOOK_NOT_FOUND", "message": "번역 결과를 찾을 수 없습니다."},
            )
        if book.owner_user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "FORBIDDEN", "message": "접근 권한이 없습니다."},
            )
        if book.status != "FAILED":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "NOT_FAILED",
                    "message": "실패 상태의 번역만 재시도할 수 있습니다.",
                },
            )
        await _check_daily_limit(self.book_repo, user_id)
        if not book.source_file:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "NO_SOURCE_FILE",
                    "message": "원본 파일 정보가 없습니다. 새로 번역을 시작해주세요.",
                },
            )

        now = datetime.now(UTC)
        ai_user = user_id

        page = await self.page_repo.get_first_by_book(book_id)

        book.status = "PENDING"
        book.updated_at = now
        book.updated_by = ai_user

        if page:
            page.status = "PENDING"
            page.ocr_text = None
            page.literal_text = None
            page.interpretive_text = None
            page.updated_at = now
            page.updated_by = ai_user

        pipeline_run = PipelineRun(
            trigger_type="TRANSLATOR",
            triggered_by=user_id,
            book_id=book.id,
            status="PENDING",
            created_at=now,
        )
        await self.run_repo.create(pipeline_run)
        await self.db.commit()

        background_tasks.add_task(
            run_pipeline, book.id, book.source_file.local_path, pipeline_run.id
        )

        return TranslateStartResponse(book_id=book.id, status=book.status)

    async def get_book(self, book_id: str, payload: dict[str, Any]) -> BookResponse:
        book = await self.book_repo.get_by_id_with_pages(book_id)
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "BOOK_NOT_FOUND", "message": "번역 결과를 찾을 수 없습니다."},
            )
        if book.owner_user_id != payload["sub"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "FORBIDDEN", "message": "접근 권한이 없습니다."},
            )
        return _build_book_response(book)

    async def list_books(
        self, req: BookListRequest, payload: dict[str, Any]
    ) -> PageData[BookListItemResponse]:
        user_id: str = payload["sub"]
        q = req.q.strip() if req.q else None
        books, total = await self.book_repo.list_by_owner(
            user_id,
            req.page,
            req.size,
            req.status,
            req.is_favorite,
            q or None,
        )
        return PageData(
            items=[BookListItemResponse.model_validate(b) for b in books],
            total=total,
            page=req.page,
            size=req.size,
        )

    async def toggle_favorite(self, book_id: str, payload: dict[str, Any]) -> BookFavoriteResponse:
        user_id: str = payload["sub"]
        book = await self.book_repo.get_by_id(book_id)
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "BOOK_NOT_FOUND", "message": "번역 결과를 찾을 수 없습니다."},
            )
        if book.owner_user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "FORBIDDEN", "message": "권한이 없습니다."},
            )
        now = datetime.now(UTC)
        book.is_favorite = not book.is_favorite
        book.updated_at = now
        book.updated_by = user_id
        await self.db.commit()
        return BookFavoriteResponse(book_id=book_id, is_favorite=book.is_favorite)

    async def list_public_books(
        self,
        req: BookPublicListRequest,
        user_id: str | None = None,
    ) -> PageData[BookPublicListItemResponse]:
        q = req.q.strip() if req.q else None
        bm_user_id = user_id if req.bm else None
        books, total = await self.book_repo.list_completed_public(
            req.page, req.size, q or None, bm_user_id
        )

        bookmarked_ids: set[str] = set()
        if user_id and books:
            bookmarked_ids = await self.bookmark_repo.get_bookmarked_ids(
                user_id, [b.id for b in books]
            )

        items = []
        for b in books:
            item = BookPublicListItemResponse.model_validate(b)
            item.source_file_url = b.source_file.url_path if b.source_file else None
            item.owner_name = b.owner.name if b.owner else ""
            item.is_bookmarked = b.id in bookmarked_ids
            items.append(item)
        return PageData(items=items, total=total, page=req.page, size=req.size)

    async def toggle_bookmark(self, book_id: str, payload: dict[str, Any]) -> BookBookmarkResponse:
        user_id: str = payload["sub"]
        book = await self.book_repo.get_completed_public_by_id(book_id)
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "BOOK_NOT_FOUND", "message": "공개 번역 결과를 찾을 수 없습니다."},
            )
        if book.owner_user_id == user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "CANNOT_BOOKMARK_OWN",
                    "message": "본인 Book은 북마크할 수 없습니다.",
                },
            )
        existing = await self.bookmark_repo.get(user_id, book_id)
        if existing:
            await self.bookmark_repo.delete(existing)
            is_bookmarked = False
        else:
            await self.bookmark_repo.create(user_id, book_id)
            is_bookmarked = True
        await self.db.commit()
        return BookBookmarkResponse(book_id=book_id, is_bookmarked=is_bookmarked)

    async def update_book_title(
        self,
        book_id: str,
        title: str,
        payload: dict[str, Any],
    ) -> None:
        user_id: str = payload["sub"]
        book = await self.book_repo.get_by_id(book_id)
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "BOOK_NOT_FOUND", "message": "번역 결과를 찾을 수 없습니다."},
            )
        if book.owner_user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "BOOK_ACCESS_FORBIDDEN", "message": "접근 권한이 없습니다."},
            )
        now = datetime.now(UTC)
        book.title = title
        book.updated_at = now
        book.updated_by = user_id
        await self.db.commit()

    async def start_ocr(
        self,
        file_id: str,
        payload: dict[str, Any],
        background_tasks: BackgroundTasks,
    ) -> OcrStartResponse:
        user_id: str = payload["sub"]
        await _check_daily_limit(self.book_repo, user_id)

        file_entity = await _validate_image_file(self.file_repo, file_id, user_id)

        now = datetime.now(UTC)
        book = Book(
            id=await next_id("BOOK_", self.db),
            owner_user_id=user_id,
            source_file_id=file_entity.id,
            title=file_entity.original_name,
            book_type="QUICK",
            source_type="IMAGE",
            total_pages=1,
            status="PENDING",
            created_at=now,
            created_by=user_id,
            updated_at=now,
            updated_by=user_id,
        )
        await self.book_repo.create(book)

        page = BookPage(
            id=await next_id("BPAGE_", self.db),
            book_id=book.id,
            page_no=1,
            status="PENDING",
            created_at=now,
            created_by=user_id,
            updated_at=now,
            updated_by=user_id,
        )
        await self.page_repo.create(page)

        pipeline_run = PipelineRun(
            trigger_type="TRANSLATOR",
            triggered_by=user_id,
            book_id=book.id,
            status="PENDING",
            created_at=now,
        )
        await self.run_repo.create(pipeline_run)
        await self.db.commit()

        background_tasks.add_task(run_ocr_only, book.id, file_entity.local_path, pipeline_run.id)

        return OcrStartResponse(book_id=book.id, status=book.status)

    async def translate_text(
        self,
        req: TranslateTextRequest,
        payload: dict[str, Any],
        background_tasks: BackgroundTasks,
    ) -> TranslateStartResponse:
        user_id: str = payload["sub"]

        if not req.text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "TEXT_REQUIRED", "message": "번역할 텍스트를 입력해주세요."},
            )

        now = datetime.now(UTC)

        if req.book_id:
            book = await self.book_repo.get_by_id(req.book_id)
            if not book:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={"code": "BOOK_NOT_FOUND", "message": "번역 결과를 찾을 수 없습니다."},
                )
            if book.owner_user_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={"code": "BOOK_ACCESS_FORBIDDEN", "message": "접근 권한이 없습니다."},
                )
            if book.status != "OCR_COMPLETED":
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "code": "INVALID_BOOK_STATUS",
                        "message": "OCR 완료 상태의 번역만 이어서 번역할 수 있습니다.",
                    },
                )

            page = await self.page_repo.get_first_by_book(req.book_id)
            if not page:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={"code": "PAGE_NOT_FOUND", "message": "페이지를 찾을 수 없습니다."},
                )
            page.ocr_text = req.text
            page.updated_at = now
            page.updated_by = user_id

            book.status = "PENDING"
            book.updated_at = now
            book.updated_by = user_id
        else:
            await _check_daily_limit(self.book_repo, user_id)

            title = f"새로운 번역 {now.strftime('%Y-%m-%d %H:%M')}"
            book = Book(
                id=await next_id("BOOK_", self.db),
                owner_user_id=user_id,
                source_file_id=None,
                title=title,
                book_type="QUICK",
                source_type="TEXT",
                total_pages=1,
                status="PENDING",
                created_at=now,
                created_by=user_id,
                updated_at=now,
                updated_by=user_id,
            )
            await self.book_repo.create(book)

            page = BookPage(
                id=await next_id("BPAGE_", self.db),
                book_id=book.id,
                page_no=1,
                ocr_text=req.text,
                status="PENDING",
                created_at=now,
                created_by=user_id,
                updated_at=now,
                updated_by=user_id,
            )
            await self.page_repo.create(page)

        pipeline_run = PipelineRun(
            trigger_type="TRANSLATOR",
            triggered_by=user_id,
            book_id=book.id,
            status="PENDING",
            created_at=now,
        )
        await self.run_repo.create(pipeline_run)
        await self.db.commit()

        background_tasks.add_task(run_translate_only, book.id, pipeline_run.id)

        return TranslateStartResponse(book_id=book.id, status=book.status)

    async def save_page_edit(
        self,
        book_id: str,
        page_no: int,
        req: PageEditRequest,
        payload: dict[str, Any],
    ) -> PageEditResponse:
        user_id: str = payload["sub"]

        book = await self.book_repo.get_by_id(book_id)
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "BOOK_NOT_FOUND", "message": "번역 결과를 찾을 수 없습니다."},
            )
        if book.owner_user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "BOOK_ACCESS_FORBIDDEN", "message": "접근 권한이 없습니다."},
            )
        if book.status != "COMPLETED":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "EDIT_NOT_ALLOWED",
                    "message": "완료된 번역만 편집할 수 있습니다.",
                },
            )

        page = await self.page_repo.get_by_book_and_page_no(book_id, page_no)
        if not page:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "PAGE_NOT_FOUND", "message": "페이지를 찾을 수 없습니다."},
            )

        now = datetime.now(UTC)
        max_version = await self.revision_repo.get_max_version(page.id)
        new_version = max_version + 1

        page.ocr_text = req.ocr_text
        page.literal_text = req.literal_text
        page.interpretive_text = req.interpretive_text
        page.updated_at = now
        page.updated_by = user_id

        revision = PageRevision(
            page_id=page.id,
            version=new_version,
            ocr_text=req.ocr_text,
            literal_text=req.literal_text,
            interpretive_text=req.interpretive_text,
            edited_by=user_id,
            created_at=now,
        )
        try:
            await self.revision_repo.create(revision)  # flush() 내부에서 unique 충돌 가능
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "REVISION_CONFLICT",
                    "message": "동시 저장 충돌이 발생했습니다. 다시 시도해주세요.",
                },
            ) from None

        return PageEditResponse(version=new_version)

    async def get_public_book(self, book_id: str) -> BookResponse:
        book = await self.book_repo.get_completed_public_by_id(book_id)
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "BOOK_NOT_FOUND", "message": "번역 결과를 찾을 수 없습니다."},
            )
        return _build_book_response(book)

    async def list_my_completed_books(self, user_id: str) -> list[BookDropdownItemResponse]:
        books, _ = await self.book_repo.list_by_owner(user_id, page=1, size=100, status="COMPLETED")
        result = []
        for b in books:
            book_with_file = await self.book_repo.get_by_id_with_source_file(b.id)
            source_file_url = (
                book_with_file.source_file.url_path
                if book_with_file and book_with_file.source_file
                else None
            )
            result.append(
                BookDropdownItemResponse(
                    book_id=b.id,
                    title=b.title,
                    source_file_url=source_file_url,
                    created_at=b.created_at,
                )
            )
        return result
