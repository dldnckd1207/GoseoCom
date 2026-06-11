from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.files.models import File
from app.core.user.models import User
from app.db.base import Base
from app.db.mixins import SoftDeleteMixin, TimestampMixin


class Book(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "ai_tn_book"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)  # BOOK_00000001
    owner_user_id: Mapped[str] = mapped_column(
        ForeignKey("com_tn_user.id", ondelete="RESTRICT"), nullable=False
    )
    source_file_id: Mapped[str | None] = mapped_column(
        ForeignKey("com_tn_file.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    book_type: Mapped[str] = mapped_column(String(20), nullable=False)  # QUICK | USER_CREATED
    source_type: Mapped[str] = mapped_column(String(20), nullable=False)  # IMAGE | PDF
    total_pages: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="PENDING", server_default="PENDING"
    )  # PENDING | OCR_PROCESSING | TRANSLATING | COMPLETED | FAILED
    is_favorite: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )  # Phase 2
    share_token: Mapped[str | None] = mapped_column(String(100), nullable=True)  # Phase 2
    summary_text: Mapped[str | None] = mapped_column(Text, nullable=True)  # Phase 2
    keywords: Mapped[list[dict[str, object]] | None] = mapped_column(
        JSONB, nullable=True
    )  # Phase 2

    source_file: Mapped[File | None] = relationship(
        "File", foreign_keys=[source_file_id], lazy="select"
    )
    owner: Mapped[User] = relationship("User", foreign_keys=[owner_user_id], lazy="select")
    pages: Mapped[list["BookPage"]] = relationship("BookPage", back_populates="book")

    __table_args__ = (
        Index("ix_book_owner", "owner_user_id", "del_yn", "created_at"),
        Index("ix_book_status", "status"),
        UniqueConstraint("share_token", name="uq_book_share_token"),
    )


class BookPage(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "ai_tn_book_page"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)  # BPAGE_00000001
    book_id: Mapped[str] = mapped_column(
        ForeignKey("ai_tn_book.id", ondelete="RESTRICT"), nullable=False
    )
    page_no: Mapped[int] = mapped_column(Integer, nullable=False)
    ocr_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    ocr_engine: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )  # GOOGLE_VISION | PADDLE
    ocr_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    literal_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    interpretive_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    translator_engine: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )  # GEMINI | CLAUDE
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="PENDING", server_default="PENDING"
    )

    book: Mapped["Book"] = relationship("Book", back_populates="pages")

    __table_args__ = (
        UniqueConstraint("book_id", "page_no", name="uq_book_page_no"),
        Index("ix_book_page_book", "book_id"),
    )


class PageRevision(Base):
    """번역 수정 이력 — append-only History 테이블 (Phase 2)"""

    __tablename__ = "ai_th_page_revision"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    page_id: Mapped[str] = mapped_column(
        ForeignKey("ai_tn_book_page.id", ondelete="RESTRICT"), nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    ocr_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    literal_text: Mapped[str] = mapped_column(Text, nullable=False)
    interpretive_text: Mapped[str] = mapped_column(Text, nullable=False)
    edited_by: Mapped[str] = mapped_column(
        ForeignKey("com_tn_user.id", ondelete="RESTRICT"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("ix_page_revision_page", "page_id", "version"),
        UniqueConstraint("page_id", "version", name="uq_page_revision_version"),
    )


class BookBookmark(Base):
    """공개 Book 북마크 — 로그인 사용자가 타인 공개 Book 저장"""

    __tablename__ = "ai_tn_book_bookmark"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(
        ForeignKey("com_tn_user.id", ondelete="CASCADE"), nullable=False
    )
    book_id: Mapped[str] = mapped_column(
        ForeignKey("ai_tn_book.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "book_id", name="uq_book_bookmark_user_book"),
        Index("ix_book_bookmark_user", "user_id"),
    )


class PipelineRun(Base):
    """파이프라인 실행 이력 — append-only History 테이블"""

    __tablename__ = "ai_th_pipeline_run"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    trigger_type: Mapped[str] = mapped_column(String(20), nullable=False)  # TRANSLATOR | AUTO_REPLY
    triggered_by: Mapped[str | None] = mapped_column(
        ForeignKey("com_tn_user.id", ondelete="RESTRICT"), nullable=True
    )
    book_id: Mapped[str | None] = mapped_column(
        ForeignKey("ai_tn_book.id", ondelete="RESTRICT"), nullable=True
    )
    post_id: Mapped[str | None] = mapped_column(
        ForeignKey("cms_tn_post.id", ondelete="RESTRICT"), nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="PENDING", server_default="PENDING"
    )  # PENDING | RUNNING | COMPLETED | FAILED | TIMEOUT
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    total_cnt: Mapped[int | None] = mapped_column(Integer, nullable=True)
    success_cnt: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fail_cnt: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_msg: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_stack: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("ix_pipeline_run_book", "book_id"),
        Index("ix_pipeline_run_post", "post_id"),
        Index("ix_pipeline_run_status", "status"),
        Index("ix_pipeline_run_trigger", "trigger_type"),
        Index("ix_pipeline_run_created", "created_at"),
    )
