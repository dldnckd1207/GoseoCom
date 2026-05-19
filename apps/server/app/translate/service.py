from datetime import UTC, date, datetime
from typing import Any

from fastapi import BackgroundTasks, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.common.id_generator import next_id
from app.core.common.response import PageData
from app.core.files.repository import FileRepository
from app.translate.models import Book, BookPage, PipelineRun
from app.translate.pipeline.runner import run_pipeline
from app.translate.repository import BookPageRepository, BookRepository, PipelineRunRepository
from app.translate.schemas import (
    BookListItemResponse,
    BookListRequest,
    BookResponse,
    TranslateStartResponse,
)

_MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB


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


class TranslateService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.book_repo = BookRepository(db)
        self.page_repo = BookPageRepository(db)
        self.run_repo = PipelineRunRepository(db)
        self.file_repo = FileRepository(db)

    async def start_translate(
        self,
        file_id: str,
        payload: dict[str, Any],
        background_tasks: BackgroundTasks,
    ) -> TranslateStartResponse:
        user_id: str = payload["sub"]
        await _check_daily_limit(self.book_repo, user_id)

        file_entity = await self.file_repo.get_by_id(file_id)
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
        books, total = await self.book_repo.list_by_owner(user_id, req.page, req.size, req.status)
        return PageData(
            items=[BookListItemResponse.model_validate(b) for b in books],
            total=total,
            page=req.page,
            size=req.size,
        )
