from datetime import date

from sqlalchemy import (
    Boolean,
    Date,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import SoftDeleteMixin, TimestampMixin


class LearnChatSession(Base, TimestampMixin, SoftDeleteMixin):
    """학습 워크스페이스 채팅 세션 — (user, book, type)당 1개를 재사용한다."""

    __tablename__ = "ai_tn_learn_session"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)  # LSES_00000001
    user_id: Mapped[str] = mapped_column(
        ForeignKey("com_tn_user.id", ondelete="RESTRICT"), nullable=False
    )
    book_id: Mapped[str] = mapped_column(
        ForeignKey("ai_tn_book.id", ondelete="RESTRICT"), nullable=False
    )
    session_type: Mapped[str] = mapped_column(String(20), nullable=False)  # DOC_QA | TUTOR

    __table_args__ = (
        UniqueConstraint("user_id", "book_id", "session_type", name="uq_learn_session_user_book"),
        Index("ix_learn_session_user", "user_id", "book_id"),
        Index("ix_learn_session_book", "book_id"),
    )


class LearnChatMessage(Base, TimestampMixin):
    """학습 채팅 메시지 — 세션에 append되는 대화 본문"""

    __tablename__ = "ai_tn_learn_message"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)  # LMSG_00000001
    session_id: Mapped[str] = mapped_column(
        ForeignKey("ai_tn_learn_session.id", ondelete="RESTRICT"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(10), nullable=False)  # USER | AI
    content: Mapped[str] = mapped_column(Text, nullable=False)

    __table_args__ = (Index("ix_learn_message_session", "session_id", "created_at"),)


class LearnFlashcard(Base, TimestampMixin, SoftDeleteMixin):
    """AI 암기 카드 — 생성 시 기존 세트를 soft delete 후 교체한다."""

    __tablename__ = "ai_tn_learn_flashcard"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)  # LCARD_00000001
    user_id: Mapped[str] = mapped_column(
        ForeignKey("com_tn_user.id", ondelete="RESTRICT"), nullable=False
    )
    book_id: Mapped[str] = mapped_column(
        ForeignKey("ai_tn_book.id", ondelete="RESTRICT"), nullable=False
    )
    term: Mapped[str] = mapped_column(String(200), nullable=False)
    meaning: Mapped[str] = mapped_column(Text, nullable=False)
    card_type: Mapped[str] = mapped_column(
        String(30), nullable=False, default="단어 카드", server_default="단어 카드"
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    known_yn: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )

    __table_args__ = (
        Index("ix_learn_flashcard_user", "user_id", "book_id", "del_yn"),
        Index("ix_learn_flashcard_book", "book_id"),
    )


class LearnStudyProgress(Base, TimestampMixin):
    """학습 진행도 — 사용자별 전역 1행 (XP/연속학습/복습 통계)"""

    __tablename__ = "ai_tn_learn_progress"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)  # LPRG_00000001
    user_id: Mapped[str] = mapped_column(
        ForeignKey("com_tn_user.id", ondelete="RESTRICT"), nullable=False
    )
    xp: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    streak: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    reviewed_cnt: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    correct_cnt: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    last_study_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    __table_args__ = (UniqueConstraint("user_id", name="uq_learn_progress_user"),)
