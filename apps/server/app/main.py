import asyncio
import contextlib
import logging
import logging.config
import logging.handlers
from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import update

from app.auth.router import router as auth_router
from app.auth.router import users_router
from app.board.admin_comment_router import admin_comment_router
from app.board.admin_router import admin_router as board_admin_router
from app.board.auto_reply_pipeline import auto_reply_scheduler
from app.board.comment_filter_scheduler import comment_filter_scheduler
from app.board.comment_router import comment_router
from app.board.models import Post
from app.board.post_admin_router import admin_router as post_admin_router
from app.board.post_router import board_upload_router, post_router
from app.board.router import router as board_router
from app.config import settings
from app.core.common.enums import AppEnv
from app.core.csrf import CSRFMiddleware
from app.core.files.router import router as files_router
from app.core.user.admin_router import admin_router as user_admin_router
from app.db.session import AsyncSessionLocal
from app.learn.router import router as learn_router
from app.translate.admin_router import admin_router as translate_admin_router
from app.translate.models import Book, BookPage, PipelineRun
from app.translate.router import router as translate_router

logging.config.dictConfig(
    {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s %(levelname)s %(name)s — %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": "logs/app.log",
                "maxBytes": 10 * 1024 * 1024,
                "backupCount": 5,
                "formatter": "default",
                "encoding": "utf-8",
            },
        },
        "loggers": {
            "app": {
                "handlers": ["console", "file"],
                "level": "INFO",
                "propagate": False,
            },
        },
        "root": {
            "handlers": ["console"],
            "level": "WARNING",
        },
    }
)

_STALE_BOOK_STATUSES = ("PENDING", "OCR_PROCESSING", "TRANSLATING")


async def _cleanup_stale_jobs() -> None:
    """서버 재시작 시 중단된 작업을 FAILED로 정리한다."""
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
        # RUNNING 상태 자동 답변 게시글 → FAILED (PENDING은 다음 tick에서 정상 처리)
        await db.execute(
            update(Post)
            .where(Post.auto_reply_status == "RUNNING")
            .values(auto_reply_status="FAILED", updated_at=now, updated_by=ai_user)
        )
        await db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    await _cleanup_stale_jobs()
    auto_reply_task = asyncio.create_task(auto_reply_scheduler())
    filter_task = asyncio.create_task(comment_filter_scheduler())
    yield
    auto_reply_task.cancel()
    filter_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await auto_reply_task
    with contextlib.suppress(asyncio.CancelledError):
        await filter_task


# 운영 환경에서는 Swagger/ReDoc/OpenAPI 스키마를 노출하지 않는다.
_is_prod = settings.app_env == AppEnv.PRODUCTION

app = FastAPI(
    title="Haedok AI API",
    description="한국 고서 OCR + AI 번역 서비스",
    version="0.1.0",
    docs_url=None if _is_prod else "/docs",
    redoc_url=None if _is_prod else "/redoc",
    openapi_url=None if _is_prod else "/openapi.json",
    lifespan=lifespan,
)

# CSRF는 CORS보다 먼저 등록 → CORS가 가장 바깥(에러 응답에도 CORS 헤더 부여).
# 개발 환경에서는 비활성화(교차 출처 SSR 편의). staging/prod에서만 enforce.
app.add_middleware(CSRFMiddleware, enabled=settings.app_env != AppEnv.DEVELOPMENT)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


@app.middleware("http")
async def no_cache_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """API/Auth 응답 브라우저 캐싱 금지.

    Cache-Control 부재 시 브라우저가 GET 응답을 디스크 캐시에서 재사용해
    오래된 API 데이터가 보이거나, 캐시된 OAuth 리다이렉트의 만료된 state로
    INVALID_STATE가 발생한다. /files/ 등 정적 리소스는 캐싱 이점 유지를 위해 제외.
    """
    response = await call_next(request)
    if request.url.path.startswith(("/api/", "/auth/")):
        response.headers["Cache-Control"] = "no-store"
    return response


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
app.include_router(user_admin_router)
app.include_router(board_router)
app.include_router(board_admin_router)
app.include_router(post_router)
app.include_router(post_admin_router)
app.include_router(board_upload_router)
app.include_router(comment_router)
app.include_router(admin_comment_router)
app.include_router(files_router)
app.include_router(translate_router)
app.include_router(translate_admin_router)
app.include_router(learn_router)

# 개발용 라우터 (dev 환경만)
if settings.app_env == AppEnv.DEVELOPMENT:
    from app.auth.dev_router import dev_router

    app.include_router(dev_router)


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
