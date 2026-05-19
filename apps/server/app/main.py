from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import update

from app.auth.router import router as auth_router
from app.auth.router import users_router
from app.board.admin_router import admin_router as board_admin_router
from app.board.comment_router import comment_router
from app.board.post_router import board_upload_router, post_router
from app.board.router import router as board_router
from app.config import settings
from app.core.common.enums import AppEnv
from app.core.files.router import router as files_router
from app.db.session import AsyncSessionLocal
from app.translate.models import Book, BookPage, PipelineRun
from app.translate.router import router as translate_router

_STALE_BOOK_STATUSES = ("PENDING", "OCR_PROCESSING", "TRANSLATING")


async def _cleanup_stale_jobs() -> None:
    """서버 재시작 시 중단된 번역 작업을 FAILED로 정리한다."""
    now = datetime.now(UTC)
    ai_user = settings.ai_agent_user_id
    async with AsyncSessionLocal() as db:
        await db.execute(
            update(Book)
            .where(Book.status.in_(_STALE_BOOK_STATUSES), Book.del_yn.is_(False))
            .values(status="FAILED", updated_at=now, updated_by=ai_user)
        )
        await db.execute(
            update(BookPage)
            .where(BookPage.status.in_(("PENDING", "OCR_PROCESSING")), BookPage.del_yn.is_(False))
            .values(status="FAILED", updated_at=now, updated_by=ai_user)
        )
        await db.execute(
            update(PipelineRun)
            .where(PipelineRun.status.in_(("PENDING", "RUNNING")))
            .values(status="FAILED", error_msg="서버 재시작으로 인해 중단된 작업")
        )
        await db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    await _cleanup_stale_jobs()
    yield


app = FastAPI(
    title="Haedok AI API",
    description="한국 고서 OCR + AI 번역 서비스",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """앱 레벨 예외를 공통 응답 포맷으로 변환"""
    detail: dict[str, Any] = exc.detail if isinstance(exc.detail, dict) else {}
    code: str = detail.get("code", "ERROR")
    message: str = detail.get("message", str(exc.detail))
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "header": {"success": False, "code": code, "message": message},
            "body": {"data": None},
        },
    )


# 라우터 등록
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(board_router)
app.include_router(board_admin_router)
app.include_router(post_router)
app.include_router(board_upload_router)
app.include_router(comment_router)
app.include_router(files_router)
app.include_router(translate_router)

# 개발용 라우터 (dev 환경만)
if settings.app_env == AppEnv.DEVELOPMENT:
    from app.auth.dev_router import dev_router

    app.include_router(dev_router)


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
