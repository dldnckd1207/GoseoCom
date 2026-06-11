"""악성 댓글 AI 필터링 — 5분 주기 스케줄러"""

import asyncio
import logging
from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.board.comment_filter import run_filter
from app.board.models import Comment
from app.config import settings
from app.db.session import AsyncSessionLocal

logger = logging.getLogger(__name__)


async def _find_pending_comments(db: AsyncSession, limit: int) -> list[Comment]:
    """filter_status='PENDING', del_yn=False, AI 댓글 제외, 오래된 순 limit건."""
    result = await db.execute(
        select(Comment)
        .where(
            Comment.filter_status == "PENDING",
            Comment.del_yn.is_(False),
            Comment.user_id != settings.ai_agent_user_id,
        )
        .order_by(Comment.created_at.asc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def _process_comment(db: AsyncSession, comment: Comment, now: datetime) -> None:
    """단일 댓글 악성 여부 판별 후 DB 업데이트.

    성공: filter_status → CLEAN or FLAGGED
    실패: PENDING 유지, 오류 로그 (다음 배치에서 재시도)
    """
    try:
        is_malicious, reason, confidence = await run_filter(comment.content)
    except Exception as exc:
        logger.warning(
            "댓글 필터링 실패 (PENDING 유지). comment_id=%s error=%s",
            comment.id,
            str(exc)[:200],
        )
        return

    if is_malicious:
        await db.execute(
            update(Comment)
            .where(Comment.id == comment.id)
            .values(
                filter_status="FLAGGED",
                is_filtered=True,
                filter_reason=f"{reason[:200]} (confidence: {confidence:.2f})",
                filtered_at=now,
            )
        )
    else:
        await db.execute(
            update(Comment).where(Comment.id == comment.id).values(filter_status="CLEAN")
        )
    await db.commit()


async def run_filter_batch() -> None:
    """스케줄러 1회 실행: PENDING 댓글 배치 처리."""
    async with AsyncSessionLocal() as db:
        comments = await _find_pending_comments(db, settings.scheduler_comment_filter_batch_size)
        now = datetime.now(UTC)
        for comment in comments:
            await _process_comment(db, comment, now)


async def comment_filter_scheduler() -> None:
    """lifespan에서 create_task로 실행되는 무한 루프 스케줄러."""
    while True:
        await asyncio.sleep(settings.scheduler_comment_filter_interval_seconds)
        try:
            await run_filter_batch()
        except Exception:
            logger.exception("댓글 필터링 스케줄러 실행 중 오류가 발생했습니다.")
