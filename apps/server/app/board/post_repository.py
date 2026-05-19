"""게시글 Repository — DB 쿼리"""

from datetime import UTC, datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.board.models import Post, PostHistory


class PostRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list(
        self,
        board_ids: list[str],
        keyword: str | None,
        page: int,
        size: int,
    ) -> tuple[list[Post], int]:
        conditions = [
            Post.board_id.in_(board_ids),
            Post.del_yn.is_(False),
            Post.parent_id.is_(None),  # 원글만 (답글 제외)
        ]
        if keyword:
            conditions.append(Post.title.ilike(f"%{keyword}%"))

        base = (
            select(Post).where(*conditions).order_by(Post.notice_yn.desc(), Post.created_at.desc())
        )
        total_result = await self.db.execute(select(func.count()).select_from(base.subquery()))
        total: int = total_result.scalar_one()
        result = await self.db.execute(base.offset((page - 1) * size).limit(size))
        return list(result.scalars().all()), total

    async def get_by_id(self, post_id: str) -> Post | None:
        result = await self.db.execute(
            select(Post).where(Post.id == post_id, Post.del_yn.is_(False))
        )
        return result.scalar_one_or_none()

    async def create(self, post: Post) -> Post:
        self.db.add(post)
        await self.db.flush()
        return post

    async def update_view_count(self, post_id: str) -> None:
        await self.db.execute(
            update(Post).where(Post.id == post_id).values(view_count=Post.view_count + 1)
        )

    async def increment_comment_count(self, post_id: str) -> None:
        await self.db.execute(
            update(Post).where(Post.id == post_id).values(comment_count=Post.comment_count + 1)
        )

    async def decrement_comment_count(self, post_id: str) -> None:
        await self.db.execute(
            update(Post)
            .where(Post.id == post_id, Post.comment_count > 0)
            .values(comment_count=Post.comment_count - 1)
        )

    async def soft_delete(self, post: Post, deleted_by: str) -> None:
        now = datetime.now(UTC)
        post.del_yn = True
        post.deleted_at = now
        post.deleted_by = deleted_by
        await self.db.flush()


class PostHistoryRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_last_version(self, post_id: str) -> int:
        result = await self.db.execute(
            select(func.coalesce(func.max(PostHistory.version), 0)).where(
                PostHistory.post_id == post_id
            )
        )
        return result.scalar_one()

    async def insert(self, history: PostHistory) -> None:
        self.db.add(history)
        await self.db.flush()
