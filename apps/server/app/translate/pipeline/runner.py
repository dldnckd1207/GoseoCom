import traceback
from datetime import UTC, datetime

from app.config import settings
from app.db.session import AsyncSessionLocal
from app.translate.pipeline.analyzer import run_analyze
from app.translate.pipeline.ocr import run_ocr
from app.translate.pipeline.translator import run_translate
from app.translate.repository import BookPageRepository, BookRepository, PipelineRunRepository


async def run_ocr_only(book_id: str, file_local_path: str, pipeline_run_id: int) -> None:
    async with AsyncSessionLocal() as db:
        book_repo = BookRepository(db)
        page_repo = BookPageRepository(db)
        run_repo = PipelineRunRepository(db)

        book = await book_repo.get_by_id(book_id)
        page = await page_repo.get_first_by_book(book_id)
        pipeline_run = await run_repo.get_by_id(pipeline_run_id)

        if not book or not page or not pipeline_run:
            return

        ai_user = settings.ai_agent_user_id
        started_at = datetime.now(UTC)

        pipeline_run.status = "RUNNING"
        pipeline_run.started_at = started_at
        await db.commit()

        try:
            book.status = "OCR_PROCESSING"
            book.updated_at = datetime.now(UTC)
            book.updated_by = ai_user
            await db.commit()

            ocr_text = await run_ocr(file_local_path)
            completed_at = datetime.now(UTC)

            page.ocr_text = ocr_text
            page.ocr_engine = "GOOGLE_VISION"
            page.updated_at = completed_at
            page.updated_by = ai_user

            if not ocr_text.strip():
                page.status = "NO_TEXT"
                book.status = "COMPLETED"
            else:
                page.status = "COMPLETED"
                book.status = "OCR_COMPLETED"

            book.updated_at = completed_at
            book.updated_by = ai_user
            pipeline_run.status = "COMPLETED"
            pipeline_run.completed_at = completed_at
            pipeline_run.duration_ms = int((completed_at - started_at).total_seconds() * 1000)
            pipeline_run.total_cnt = 1
            pipeline_run.success_cnt = 1
            await db.commit()

        except Exception as exc:
            failed_at = datetime.now(UTC)
            book.status = "FAILED"
            book.updated_at = failed_at
            book.updated_by = ai_user
            page.status = "FAILED"
            page.updated_at = failed_at
            page.updated_by = ai_user
            pipeline_run.status = "FAILED"
            pipeline_run.fail_cnt = 1
            pipeline_run.error_msg = str(exc)[:500]
            pipeline_run.error_stack = traceback.format_exc()[:2000]
            try:
                await db.commit()
            except Exception:
                await db.rollback()


async def run_translate_only(book_id: str, pipeline_run_id: int) -> None:
    async with AsyncSessionLocal() as db:
        book_repo = BookRepository(db)
        page_repo = BookPageRepository(db)
        run_repo = PipelineRunRepository(db)

        book = await book_repo.get_by_id(book_id)
        page = await page_repo.get_first_by_book(book_id)
        pipeline_run = await run_repo.get_by_id(pipeline_run_id)

        if not book or not page or not pipeline_run:
            return

        ai_user = settings.ai_agent_user_id
        started_at = datetime.now(UTC)

        pipeline_run.status = "RUNNING"
        pipeline_run.started_at = started_at

        book.status = "TRANSLATING"
        book.updated_at = datetime.now(UTC)
        book.updated_by = ai_user
        await db.commit()

        try:
            ocr_text = page.ocr_text or ""
            literal_text, interpretive_text = await run_translate(ocr_text)

            try:
                summary, keywords = await run_analyze(ocr_text, interpretive_text)
                book.summary_text = summary or None
                book.keywords = keywords or None
            except Exception:
                pass

            completed_at = datetime.now(UTC)

            page.literal_text = literal_text
            page.interpretive_text = interpretive_text
            page.translator_engine = settings.translator_engine.value.upper()
            page.status = "COMPLETED"
            page.updated_at = completed_at
            page.updated_by = ai_user

            book.status = "COMPLETED"
            book.updated_at = completed_at
            book.updated_by = ai_user

            pipeline_run.status = "COMPLETED"
            pipeline_run.completed_at = completed_at
            pipeline_run.duration_ms = int((completed_at - started_at).total_seconds() * 1000)
            pipeline_run.total_cnt = 1
            pipeline_run.success_cnt = 1
            await db.commit()

        except Exception as exc:
            failed_at = datetime.now(UTC)
            book.status = "FAILED"
            book.updated_at = failed_at
            book.updated_by = ai_user
            page.status = "FAILED"
            page.updated_at = failed_at
            page.updated_by = ai_user
            pipeline_run.status = "FAILED"
            pipeline_run.fail_cnt = 1
            pipeline_run.error_msg = str(exc)[:500]
            pipeline_run.error_stack = traceback.format_exc()[:2000]
            try:
                await db.commit()
            except Exception:
                await db.rollback()


async def run_pipeline(book_id: str, file_local_path: str, pipeline_run_id: int) -> None:
    async with AsyncSessionLocal() as db:
        book_repo = BookRepository(db)
        page_repo = BookPageRepository(db)
        run_repo = PipelineRunRepository(db)

        book = await book_repo.get_by_id(book_id)
        page = await page_repo.get_first_by_book(book_id)
        pipeline_run = await run_repo.get_by_id(pipeline_run_id)

        if not book or not page or not pipeline_run:
            return

        ai_user = settings.ai_agent_user_id
        started_at = datetime.now(UTC)

        pipeline_run.status = "RUNNING"
        pipeline_run.started_at = started_at
        await db.commit()

        try:
            book.status = "OCR_PROCESSING"
            book.updated_at = datetime.now(UTC)
            book.updated_by = ai_user
            await db.commit()

            ocr_text = await run_ocr(file_local_path)
            page.ocr_text = ocr_text
            page.ocr_engine = "GOOGLE_VISION"
            page.updated_at = datetime.now(UTC)
            page.updated_by = ai_user
            await db.commit()

            if not ocr_text.strip():
                page.status = "NO_TEXT"
                book.status = "COMPLETED"
                completed_at = datetime.now(UTC)
                book.updated_at = completed_at
                book.updated_by = ai_user
                page.updated_at = completed_at
                page.updated_by = ai_user
                pipeline_run.status = "COMPLETED"
                pipeline_run.completed_at = completed_at
                pipeline_run.duration_ms = int((completed_at - started_at).total_seconds() * 1000)
                pipeline_run.total_cnt = 1
                pipeline_run.success_cnt = 1
                await db.commit()
                return

            book.status = "TRANSLATING"
            book.updated_at = datetime.now(UTC)
            book.updated_by = ai_user
            await db.commit()

            literal_text, interpretive_text = await run_translate(ocr_text)

            try:
                summary, keywords = await run_analyze(ocr_text, interpretive_text)
                book.summary_text = summary or None
                book.keywords = keywords or None
            except Exception:
                pass

            completed_at = datetime.now(UTC)

            page.literal_text = literal_text
            page.interpretive_text = interpretive_text
            page.translator_engine = settings.translator_engine.value.upper()
            page.status = "COMPLETED"
            page.updated_at = completed_at
            page.updated_by = ai_user

            book.status = "COMPLETED"
            book.updated_at = completed_at
            book.updated_by = ai_user

            pipeline_run.status = "COMPLETED"
            pipeline_run.completed_at = completed_at
            pipeline_run.duration_ms = int((completed_at - started_at).total_seconds() * 1000)
            pipeline_run.total_cnt = 1
            pipeline_run.success_cnt = 1
            await db.commit()

        except Exception as exc:
            failed_at = datetime.now(UTC)
            book.status = "FAILED"
            book.updated_at = failed_at
            book.updated_by = ai_user
            page.status = "FAILED"
            page.updated_at = failed_at
            page.updated_by = ai_user
            pipeline_run.status = "FAILED"
            pipeline_run.fail_cnt = 1
            pipeline_run.error_msg = str(exc)[:500]
            pipeline_run.error_stack = traceback.format_exc()[:2000]
            try:
                await db.commit()
            except Exception:
                await db.rollback()
