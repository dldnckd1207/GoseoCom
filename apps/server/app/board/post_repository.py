"""게시글 Repository — DB 쿼리"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from sqlalchemy import ColumnElement, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.board.models import Post, PostHistory


class PostRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_by_boards(
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
        result = await self.db.execute(
            base.options(selectinload(Post.category)).offset((page - 1) * size).limit(size)
        )
        return list(result.scalars().all()), total

    async def get_by_id(self, post_id: str) -> Post | None:
        result = await self.db.execute(
            select(Post)
            .options(selectinload(Post.category))
            .where(Post.id == post_id, Post.del_yn.is_(False))
        )
        return result.scalar_one_or_none()

    async def admin_list(
        self,
        *,
        keyword: str | None,
        board_id: str | None,
        author_keyword: str | None,
        notice_yn: bool | None,
        deleted_status: Literal["active", "deleted", "all"],
        page: int,
        size: int,
    ) -> tuple[list[Post], int]:
        conditions: list[ColumnElement[bool]] = [Post.parent_id.is_(None)]
        if keyword:
            like = f"%{keyword}%"
            conditions.append(or_(Post.title.ilike(like), Post.content.ilike(like)))
        if board_id:
            conditions.append(Post.board_id == board_id)
        if author_keyword:
            like = f"%{author_keyword}%"
            conditions.append(or_(Post.author_name.ilike(like), Post.user_id.ilike(like)))
        if notice_yn is not None:
            conditions.append(Post.notice_yn.is_(notice_yn))
        if deleted_status == "active":
            conditions.append(Post.del_yn.is_(False))
        elif deleted_status == "deleted":
            conditions.append(Post.del_yn.is_(True))

        base = (
            select(Post).where(*conditions).order_by(Post.notice_yn.desc(), Post.created_at.desc())
        )
        total_result = await self.db.execute(select(func.count()).select_from(base.subquery()))
        total: int = total_result.scalar_one()
        result = await self.db.execute(
            base.options(selectinload(Post.board), selectinload(Post.category))
            .offset((page - 1) * size)
            .limit(size)
        )
        return list(result.scalars().all()), total

    async def admin_get_by_id(self, post_id: str) -> Post | None:
        result = await self.db.execute(
            select(Post)
            .options(selectinload(Post.board), selectinload(Post.category))
            .where(Post.id == post_id)
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

    async def restore(self, post: Post, updated_by: str) -> None:
        now = datetime.now(UTC)
        post.del_yn = False
        post.deleted_at = None
        post.deleted_by = None
        post.updated_at = now
        post.updated_by = updated_by
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
