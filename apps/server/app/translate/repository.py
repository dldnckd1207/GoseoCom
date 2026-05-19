from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.translate.models import Book, BookPage, PipelineRun


class BookRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, book: Book) -> Book:
        self.db.add(book)
        await self.db.flush()
        return book

    async def get_by_id(self, book_id: str) -> Book | None:
        result = await self.db.execute(
            select(Book).where(Book.id == book_id, Book.del_yn.is_(False))
        )
        return result.scalar_one_or_none()

    async def get_by_id_with_pages(self, book_id: str) -> Book | None:
        result = await self.db.execute(
            select(Book)
            .options(selectinload(Book.pages), selectinload(Book.source_file))
            .where(Book.id == book_id, Book.del_yn.is_(False))
        )
        return result.scalar_one_or_none()

    async def count_today_by_owner(self, owner_user_id: str, today: date) -> int:
        result = await self.db.execute(
            select(func.count())
            .select_from(Book)
            .where(
                Book.owner_user_id == owner_user_id,
                Book.del_yn.is_(False),
                func.date(Book.created_at) == today,
            )
        )
        return result.scalar_one()

    async def get_by_id_with_source_file(self, book_id: str) -> Book | None:
        result = await self.db.execute(
            select(Book)
            .options(selectinload(Book.source_file))
            .where(Book.id == book_id, Book.del_yn.is_(False))
        )
        return result.scalar_one_or_none()

    async def list_by_owner(
        self,
        owner_user_id: str,
        page: int,
        size: int,
        status: str | None,
    ) -> tuple[list[Book], int]:
        conditions = [Book.owner_user_id == owner_user_id, Book.del_yn.is_(False)]
        if status:
            conditions.append(Book.status == status)
        base = select(Book).where(*conditions).order_by(Book.created_at.desc())
        total_result = await self.db.execute(select(func.count()).select_from(base.subquery()))
        total: int = total_result.scalar_one()
        result = await self.db.execute(base.offset((page - 1) * size).limit(size))
        return list(result.scalars().all()), total


class BookPageRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, page: BookPage) -> BookPage:
        self.db.add(page)
        await self.db.flush()
        return page

    async def get_first_by_book(self, book_id: str) -> BookPage | None:
        result = await self.db.execute(
            select(BookPage).where(
                BookPage.book_id == book_id,
                BookPage.page_no == 1,
                BookPage.del_yn.is_(False),
            )
        )
        return result.scalar_one_or_none()


class PipelineRunRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, run: PipelineRun) -> PipelineRun:
        self.db.add(run)
        await self.db.flush()
        return run

    async def get_by_id(self, run_id: int) -> PipelineRun | None:
        result = await self.db.execute(select(PipelineRun).where(PipelineRun.id == run_id))
        return result.scalar_one_or_none()
