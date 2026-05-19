"""댓글 Repository — DB 쿼리"""

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.board.models import Comment


class CommentRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_roots(self, post_id: str, page: int, size: int) -> tuple[list[Comment], int]:
        """root 댓글 조회 — del_yn 무관 (placeholder 포함)"""
        base = (
            select(Comment)
            .where(Comment.post_id == post_id, Comment.parent_id.is_(None))
            .order_by(Comment.created_at.asc())
        )
        total_result = await self.db.execute(select(func.count()).select_from(base.subquery()))
        total: int = total_result.scalar_one()
        result = await self.db.execute(base.offset((page - 1) * size).limit(size))
        return list(result.scalars().all()), total

    async def list_replies_by_roots(self, root_ids: list[str]) -> list[Comment]:
        """root id 목록으로 대댓글 일괄 조회 — del_yn=false만"""
        if not root_ids:
            return []
        result = await self.db.execute(
            select(Comment)
            .where(
                Comment.parent_id.in_(root_ids),
                Comment.del_yn.is_(False),
            )
            .order_by(Comment.created_at.asc())
        )
        return list(result.scalars().all())

    async def get_by_id_and_post(self, comment_id: str, post_id: str) -> Comment | None:
        result = await self.db.execute(
            select(Comment).where(
                Comment.id == comment_id,
                Comment.post_id == post_id,
                Comment.del_yn.is_(False),
            )
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, comment_id: str) -> Comment | None:
        result = await self.db.execute(
            select(Comment).where(
                Comment.id == comment_id,
                Comment.del_yn.is_(False),
            )
        )
        return result.scalar_one_or_none()

    async def create(self, comment: Comment) -> Comment:
        self.db.add(comment)
        await self.db.flush()
        return comment

    async def soft_delete(self, comment: Comment, deleted_by: str) -> None:
        now = datetime.now(UTC)
        comment.del_yn = True
        comment.deleted_at = now
        comment.deleted_by = deleted_by
        await self.db.flush()
