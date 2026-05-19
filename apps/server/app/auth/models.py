from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class LoginLog(Base):
    """로그인 이력 — append-only History 테이블"""

    __tablename__ = "com_th_login_log"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[str | None] = mapped_column(
        ForeignKey("com_tn_user.id", ondelete="RESTRICT"), nullable=True
    )
    login_id: Mapped[str] = mapped_column(String(255), nullable=False)  # provider email
    login_type: Mapped[str] = mapped_column(String(20), nullable=False)  # GOOGLE | KAKAO
    login_result: Mapped[str] = mapped_column(String(20), nullable=False)  # SUCCESS | FAIL
    fail_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ip_address: Mapped[str] = mapped_column(String(50), nullable=False)
    client_info: Mapped[str | None] = mapped_column(String(500), nullable=True)
    session_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("ix_login_log_user", "user_id"),
        Index("ix_login_log_created", "created_at"),
        Index("ix_login_log_result", "login_result"),
    )
