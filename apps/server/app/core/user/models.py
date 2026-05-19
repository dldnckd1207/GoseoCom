from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import SoftDeleteMixin, TimestampMixin


class User(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "com_tn_user"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)  # USR_00000001
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    profile_image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    user_level: Mapped[int] = mapped_column(
        Integer, nullable=False, default=10, server_default="10"
    )
    use_yn: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    block_yn: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    blocked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    blocked_by: Mapped[str | None] = mapped_column(
        ForeignKey("com_tn_user.id", ondelete="RESTRICT"), nullable=True
    )
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    left_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    left_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)

    oauths: Mapped[list["UserOAuth"]] = relationship("UserOAuth", back_populates="user")
    tokens: Mapped[list["UserToken"]] = relationship("UserToken", back_populates="user")

    __table_args__ = (
        Index("ix_user_level", "user_level"),
        Index("ix_user_del", "del_yn"),
        Index("ix_user_left", "left_at"),
    )


class UserOAuth(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "com_tn_user_oauth"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)  # OAUTH_00000001
    user_id: Mapped[str] = mapped_column(
        ForeignKey("com_tn_user.id", ondelete="RESTRICT"), nullable=False
    )
    provider: Mapped[str] = mapped_column(String(20), nullable=False)  # GOOGLE | KAKAO
    provider_user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    provider_email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="oauths")

    __table_args__ = (
        UniqueConstraint("provider", "provider_user_id", name="uq_user_oauth_provider"),
        Index("ix_user_oauth_user", "user_id"),
    )


class UserToken(Base):
    """Refresh Token 관리 — Rotation 패턴"""

    __tablename__ = "com_tn_user_token"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)  # UTKN_00000001
    user_id: Mapped[str] = mapped_column(
        ForeignKey("com_tn_user.id", ondelete="CASCADE"), nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False)  # HMAC-SHA256 해시
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_revoked: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    # 기기 정보 (세션 관리 화면 확장 대비)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_by: Mapped[str] = mapped_column(String(20), nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="tokens")

    __table_args__ = (
        Index("ix_user_token_user", "user_id"),
        Index("ix_user_token_hash", "token_hash"),
        Index("ix_user_token_expires", "expires_at"),
    )
