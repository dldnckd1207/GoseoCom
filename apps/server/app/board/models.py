from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import SoftDeleteMixin, TimestampMixin


class Board(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "cms_tn_board"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)  # BRD_00000001
    board_code: Mapped[str] = mapped_column(String(50), nullable=False)
    board_name: Mapped[str] = mapped_column(String(100), nullable=False)
    board_desc: Mapped[str | None] = mapped_column(String(500), nullable=True)
    board_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="LIST", server_default="LIST"
    )
    read_yn: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    guest_read_yn: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    write_yn: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    guest_write_yn: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    notice_yn: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    reply_yn: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    comment_yn: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    secret_yn: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    like_yn: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    category_yn: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    attach_yn: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    attach_ext: Mapped[str | None] = mapped_column(String(255), nullable=True)
    attach_size: Mapped[int] = mapped_column(
        Integer, nullable=False, default=10240, server_default="10240"
    )
    attach_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=5, server_default="5"
    )
    list_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=10, server_default="10"
    )
    auto_reply_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    auto_reply_delay_min: Mapped[int] = mapped_column(
        Integer, nullable=False, default=5, server_default="5"
    )
    pipeline_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    board_group: Mapped[str | None] = mapped_column(String(50), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    use_yn: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )

    posts: Mapped[list["Post"]] = relationship("Post", back_populates="board")
    categories: Mapped[list["BoardCategory"]] = relationship(
        "BoardCategory", back_populates="board"
    )

    __table_args__ = (
        UniqueConstraint("board_code", name="uq_board_code"),
        Index("ix_board_use", "use_yn", "sort_order"),
        Index("ix_board_board_group", "board_group"),
    )


class BoardCategory(Base, TimestampMixin, SoftDeleteMixin):
    """게시판 카테고리 — Phase 3 선반영"""

    __tablename__ = "cms_tn_board_category"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)  # BCAT_00000001
    board_id: Mapped[str] = mapped_column(
        ForeignKey("cms_tn_board.id", ondelete="RESTRICT"), nullable=False
    )
    category_name: Mapped[str] = mapped_column(String(100), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    use_yn: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )

    board: Mapped["Board"] = relationship("Board", back_populates="categories")

    __table_args__ = (Index("ix_board_category_board", "board_id"),)


class Post(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "cms_tn_post"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)  # POST_00000001
    board_id: Mapped[str] = mapped_column(
        ForeignKey("cms_tn_board.id", ondelete="RESTRICT"), nullable=False
    )
    category_id: Mapped[str | None] = mapped_column(
        ForeignKey("cms_tn_board_category.id", ondelete="SET NULL"), nullable=True
    )
    user_id: Mapped[str] = mapped_column(
        ForeignKey("com_tn_user.id", ondelete="RESTRICT"), nullable=False
    )
    author_name: Mapped[str] = mapped_column(String(100), nullable=False)
    parent_id: Mapped[str | None] = mapped_column(
        ForeignKey("cms_tn_post.id", ondelete="RESTRICT"), nullable=True
    )
    depth: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    notice_yn: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    secret_yn: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    view_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    like_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    comment_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    auto_reply_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="PENDING", server_default="PENDING"
    )
    auto_reply_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    board: Mapped["Board"] = relationship("Board", back_populates="posts")
    comments: Mapped[list["Comment"]] = relationship("Comment", back_populates="post")

    __table_args__ = (
        Index("ix_post_board", "board_id", "del_yn", "created_at"),
        Index("ix_post_user", "user_id"),
        Index("ix_post_parent", "parent_id"),
        Index("ix_post_auto_reply", "auto_reply_status", "created_at"),
        Index("ix_post_notice", "board_id", "notice_yn"),
        Index("ix_post_category", "category_id"),
    )


class Comment(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "cms_tn_comment"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)  # CMT_00000001
    post_id: Mapped[str] = mapped_column(
        ForeignKey("cms_tn_post.id", ondelete="RESTRICT"), nullable=False
    )
    user_id: Mapped[str] = mapped_column(
        ForeignKey("com_tn_user.id", ondelete="RESTRICT"), nullable=False
    )
    author_name: Mapped[str] = mapped_column(String(100), nullable=False)
    parent_id: Mapped[str | None] = mapped_column(
        ForeignKey("cms_tn_comment.id", ondelete="RESTRICT"), nullable=True
    )
    depth: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    content: Mapped[str] = mapped_column(Text, nullable=False)
    like_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    is_filtered: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    filter_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    filtered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    filter_reviewed_by: Mapped[str | None] = mapped_column(
        ForeignKey("com_tn_user.id", ondelete="RESTRICT"), nullable=True
    )

    post: Mapped["Post"] = relationship("Post", back_populates="comments")

    __table_args__ = (
        Index("ix_comment_post", "post_id", "del_yn", "created_at"),
        Index("ix_comment_user", "user_id"),
        Index("ix_comment_parent", "parent_id"),
        Index("ix_comment_filtered", "is_filtered"),
    )


class PostHistory(Base):
    """게시글 수정 이력 — append-only History 테이블"""

    __tablename__ = "cms_th_post_history"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    post_id: Mapped[str] = mapped_column(
        ForeignKey("cms_tn_post.id", ondelete="RESTRICT"), nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    action: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # CREATE | UPDATE | DELETE | ROLLBACK
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    changed_by: Mapped[str] = mapped_column(
        ForeignKey("com_tn_user.id", ondelete="RESTRICT"), nullable=False
    )
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (Index("ix_post_history_post", "post_id", "changed_at"),)
