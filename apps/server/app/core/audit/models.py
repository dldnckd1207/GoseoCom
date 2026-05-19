from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AdminAuditLog(Base):
    """관리자 감사 로그 — append-only History 테이블 (Phase 1 선반영, Phase 3 INSERT 시작)"""

    __tablename__ = "com_th_admin_audit_log"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(
        ForeignKey("com_tn_user.id", ondelete="RESTRICT"), nullable=False
    )
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    target_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    target_id: Mapped[str | None] = mapped_column(String(20), nullable=True)
    before_data: Mapped[dict[str, object] | None] = mapped_column(JSONB, nullable=True)
    after_data: Mapped[dict[str, object] | None] = mapped_column(JSONB, nullable=True)
    ip_address: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("ix_audit_user", "user_id"),
        Index("ix_audit_target", "target_type", "target_id"),
        Index("ix_audit_action", "action"),
        Index("ix_audit_created", "created_at"),
    )
