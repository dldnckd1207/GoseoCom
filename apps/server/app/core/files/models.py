from sqlalchemy import (
    BigInteger,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base
from app.db.mixins import SoftDeleteMixin, TimestampMixin


class File(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "com_tn_file"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)  # FILE_00000001
    uuid: Mapped[str] = mapped_column(
        UUID(as_uuid=False), nullable=False, server_default=func.gen_random_uuid(), unique=True
    )
    original_name: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_name: Mapped[str] = mapped_column(String(255), nullable=False)  # {uuid}.ext
    url_path: Mapped[str] = mapped_column(String(500), nullable=False)  # /files/{uuid}
    local_path: Mapped[str] = mapped_column(
        String(500), nullable=False
    )  # storage/files/YYYY/MM/{uuid}.ext
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    file_ext: Mapped[str] = mapped_column(String(20), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    upload_type: Mapped[str] = mapped_column(String(20), nullable=False)  # FORM | API
    download_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )

    __table_args__ = (
        UniqueConstraint("uuid", name="ix_file_uuid"),
        Index("ix_file_del", "del_yn"),
        Index("ix_file_created", "created_at"),
    )


class FileMap(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "com_tn_file_map"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)  # FMAP_00000001
    file_id: Mapped[str] = mapped_column(
        ForeignKey("com_tn_file.id", ondelete="RESTRICT"), nullable=False
    )
    target_type: Mapped[str] = mapped_column(String(20), nullable=False)  # POST | COMMENT | BOOK
    target_id: Mapped[str] = mapped_column(String(20), nullable=False)  # FK 없음 (다형성 참조)
    file_group: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # thumbnail | attachment | original
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")

    __table_args__ = (
        Index("ix_file_map_target", "target_type", "target_id"),
        Index("ix_file_map_file", "file_id"),
    )
