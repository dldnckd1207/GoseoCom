from datetime import UTC, date, datetime

from sqlalchemy import ColumnElement, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.user.models import User
from app.translate.models import Book, BookBookmark, BookPage, PageRevision, PipelineRun


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
        is_favorite: bool | None = None,
        q: str | None = None,
    ) -> tuple[list[Book], int]:
        conditions = [Book.owner_user_id == owner_user_id, Book.del_yn.is_(False)]
        if status:
            conditions.append(Book.status == status)
        if is_favorite is not None:
            conditions.append(Book.is_favorite.is_(is_favorite))
        if q:
            conditions.append(Book.title.ilike(f"%{q}%"))
        base = select(Book).where(*conditions).order_by(Book.created_at.desc())
        total_result = await self.db.execute(select(func.count()).select_from(base.subquery()))
        total: int = total_result.scalar_one()
        result = await self.db.execute(base.offset((page - 1) * size).limit(size))
        return list(result.scalars().all()), total

    async def list_completed_public(
        self,
        page: int,
        size: int,
        q: str | None = None,
        bm_user_id: str | None = None,
    ) -> tuple[list[Book], int]:
        conditions = [Book.status == "COMPLETED", Book.del_yn.is_(False)]
        if q:
            conditions.append(Book.title.ilike(f"%{q}%"))
        if bm_user_id:
            conditions.append(
                Book.id.in_(select(BookBookmark.book_id).where(BookBookmark.user_id == bm_user_id))
            )
        base = (
            select(Book)
            .options(selectinload(Book.source_file), selectinload(Book.owner))
            .where(*conditions)
            .order_by(Book.created_at.desc())
        )
        total_result = await self.db.execute(select(func.count()).select_from(base.subquery()))
        total: int = total_result.scalar_one()
        result = await self.db.execute(base.offset((page - 1) * size).limit(size))
        return list(result.scalars().all()), total

    async def get_completed_public_by_id(self, book_id: str) -> Book | None:
        result = await self.db.execute(
            select(Book)
            .options(
                selectinload(Book.pages.and_(BookPage.del_yn.is_(False))),
                selectinload(Book.source_file),
            )
            .where(Book.id == book_id, Book.del_yn.is_(False), Book.status == "COMPLETED")
        )
        return result.scalar_one_or_none()

    async def admin_list(
        self,
        page: int,
        size: int,
        keyword: str | None,
        status: str,
    ) -> tuple[list[Book], int]:
        conditions: list[ColumnElement[bool]] = [Book.del_yn.is_(False)]
        if status != "all":
            conditions.append(Book.status == status)
        if keyword:
            pattern = f"%{keyword}%"
            conditions.append(
                Book.title.ilike(pattern) | User.name.ilike(pattern) | User.email.ilike(pattern)
            )

        base = (
            select(Book)
            .join(User, User.id == Book.owner_user_id)
            .options(selectinload(Book.owner), selectinload(Book.source_file))
            .where(*conditions)
            .order_by(Book.created_at.desc(), Book.id.desc())
        )
        total_result = await self.db.execute(select(func.count()).select_from(base.subquery()))
        total: int = total_result.scalar_one()
        result = await self.db.execute(base.offset((page - 1) * size).limit(size))
        return list(result.scalars().all()), total

    async def admin_get_detail(self, book_id: str) -> Book | None:
        result = await self.db.execute(
            select(Book)
            .options(
                selectinload(Book.owner),
                selectinload(Book.source_file),
                selectinload(Book.pages.and_(BookPage.del_yn.is_(False))),
            )
            .where(Book.id == book_id, Book.del_yn.is_(False))
        )
        return result.scalar_one_or_none()


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

    async def get_by_book_and_page_no(self, book_id: str, page_no: int) -> BookPage | None:
        result = await self.db.execute(
            select(BookPage)
            .where(
                BookPage.book_id == book_id,
                BookPage.page_no == page_no,
                BookPage.del_yn.is_(False),
            )
            .with_for_update()
        )
        return result.scalar_one_or_none()


class PageRevisionRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_max_version(self, page_id: str) -> int:
        result = await self.db.execute(
            select(func.coalesce(func.max(PageRevision.version), 0)).where(
                PageRevision.page_id == page_id
            )
        )
        return result.scalar_one()

    async def create(self, revision: PageRevision) -> PageRevision:
        self.db.add(revision)
        await self.db.flush()
        return revision


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

    async def get_latest_by_book_ids(self, book_ids: list[str]) -> dict[str, PipelineRun]:
        if not book_ids:
            return {}
        result = await self.db.execute(
            select(PipelineRun)
            .where(PipelineRun.book_id.in_(book_ids))
            .order_by(
                PipelineRun.book_id.asc(), PipelineRun.created_at.desc(), PipelineRun.id.desc()
            )
        )
        latest: dict[str, PipelineRun] = {}
        for run in result.scalars().all():
            if run.book_id and run.book_id not in latest:
                latest[run.book_id] = run
        return latest

    async def list_by_book(self, book_id: str, limit: int = 10) -> list[PipelineRun]:
        result = await self.db.execute(
            select(PipelineRun)
            .where(PipelineRun.book_id == book_id)
            .order_by(PipelineRun.created_at.desc(), PipelineRun.id.desc())
            .limit(limit)
        )
        return list(result.scalars().all())


class BookBookmarkRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get(self, user_id: str, book_id: str) -> BookBookmark | None:
        result = await self.db.execute(
            select(BookBookmark).where(
                BookBookmark.user_id == user_id,
                BookBookmark.book_id == book_id,
            )
        )
        return result.scalar_one_or_none()

    async def create(self, user_id: str, book_id: str) -> BookBookmark:
        bookmark = BookBookmark(user_id=user_id, book_id=book_id, created_at=datetime.now(UTC))
        self.db.add(bookmark)
        await self.db.flush()
        return bookmark

    async def delete(self, bookmark: BookBookmark) -> None:
        await self.db.delete(bookmark)
        await self.db.flush()

    async def get_bookmarked_ids(self, user_id: str, book_ids: list[str]) -> set[str]:
        result = await self.db.execute(
            select(BookBookmark.book_id).where(
                BookBookmark.user_id == user_id,
                BookBookmark.book_id.in_(book_ids),
            )
        )
        return set(result.scalars().all())
