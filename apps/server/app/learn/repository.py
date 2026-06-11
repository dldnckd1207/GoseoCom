from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.learn.models import LearnChatMessage, LearnChatSession, LearnFlashcard, LearnStudyProgress
from app.translate.models import Book


class LearnRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ── Book (읽기 전용 — app.translate 모델 참조만) ──────────────────

    async def get_book_with_pages(self, book_id: str) -> Book | None:
        result = await self.db.execute(
            select(Book)
            .options(selectinload(Book.pages), selectinload(Book.source_file))
            .where(Book.id == book_id, Book.del_yn.is_(False))
        )
        return result.scalar_one_or_none()

    # ── ChatSession / ChatMessage ────────────────────────────────────

    async def get_session(
        self, user_id: str, book_id: str, session_type: str
    ) -> LearnChatSession | None:
        result = await self.db.execute(
            select(LearnChatSession).where(
                LearnChatSession.user_id == user_id,
                LearnChatSession.book_id == book_id,
                LearnChatSession.session_type == session_type,
                LearnChatSession.del_yn.is_(False),
            )
        )
        return result.scalar_one_or_none()

    async def list_sessions(self, user_id: str, book_id: str) -> list[LearnChatSession]:
        """(user, book)의 전체 세션을 한 번에 조회 — 워크스페이스 부트스트랩용."""
        result = await self.db.execute(
            select(LearnChatSession).where(
                LearnChatSession.user_id == user_id,
                LearnChatSession.book_id == book_id,
                LearnChatSession.del_yn.is_(False),
            )
        )
        return list(result.scalars().all())

    async def create_session(self, session: LearnChatSession) -> LearnChatSession:
        self.db.add(session)
        await self.db.flush()
        return session

    async def list_messages(self, session_id: str) -> list[LearnChatMessage]:
        result = await self.db.execute(
            select(LearnChatMessage)
            .where(LearnChatMessage.session_id == session_id)
            .order_by(LearnChatMessage.created_at.asc(), LearnChatMessage.id.asc())
        )
        return list(result.scalars().all())

    async def add_message(self, message: LearnChatMessage) -> LearnChatMessage:
        self.db.add(message)
        await self.db.flush()
        return message

    # ── Flashcard ────────────────────────────────────────────────────

    async def list_flashcards(self, user_id: str, book_id: str) -> list[LearnFlashcard]:
        result = await self.db.execute(
            select(LearnFlashcard)
            .where(
                LearnFlashcard.user_id == user_id,
                LearnFlashcard.book_id == book_id,
                LearnFlashcard.del_yn.is_(False),
            )
            .order_by(LearnFlashcard.sort_order.asc())
        )
        return list(result.scalars().all())

    async def soft_delete_flashcards(self, user_id: str, book_id: str, deleted_by: str) -> None:
        await self.db.execute(
            update(LearnFlashcard)
            .where(
                LearnFlashcard.user_id == user_id,
                LearnFlashcard.book_id == book_id,
                LearnFlashcard.del_yn.is_(False),
            )
            .values(del_yn=True, deleted_at=datetime.now(UTC), deleted_by=deleted_by)
        )

    async def add_flashcard(self, card: LearnFlashcard) -> LearnFlashcard:
        self.db.add(card)
        await self.db.flush()
        return card

    # ── StudyProgress ────────────────────────────────────────────────

    async def get_progress(self, user_id: str) -> LearnStudyProgress | None:
        result = await self.db.execute(
            select(LearnStudyProgress).where(LearnStudyProgress.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create_progress(self, progress: LearnStudyProgress) -> LearnStudyProgress:
        self.db.add(progress)
        await self.db.flush()
        return progress
