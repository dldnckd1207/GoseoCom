"""파일 Service — 파일 저장/조회"""

import os
import uuid
from datetime import UTC, datetime
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.common.id_generator import next_id
from app.core.files.models import File
from app.core.files.repository import FileRepository
from app.core.files.schemas import FileUploadResponse


class FileService:
    def __init__(self, db: AsyncSession) -> None:
        self.repo = FileRepository(db)
        self.db = db

    async def upload(
        self, file: UploadFile, user_id: str, content: bytes | None = None
    ) -> FileUploadResponse:
        if content is None:
            content = await file.read()
        file_size = len(content)
        original_name = file.filename or "unknown"
        file_ext = Path(original_name).suffix.lstrip(".").lower()
        mime_type = file.content_type or "application/octet-stream"

        file_uuid = str(uuid.uuid4())
        now = datetime.now(UTC)
        year_month = now.strftime("%Y/%m")
        stored_name = f"{file_uuid}.{file_ext}" if file_ext else file_uuid

        local_dir = Path(settings.file_local_path) / year_month
        local_dir.mkdir(parents=True, exist_ok=True)
        local_path = str(local_dir / stored_name)

        with open(local_path, "wb") as f:
            f.write(content)

        url_path = f"{settings.file_url_prefix}/{file_uuid}"

        file_id = await next_id("FILE_", self.db)
        file_entity = File(
            id=file_id,
            uuid=file_uuid,
            original_name=original_name,
            stored_name=stored_name,
            url_path=url_path,
            local_path=local_path,
            file_size=file_size,
            file_ext=file_ext,
            mime_type=mime_type,
            upload_type="API",
            created_at=now,
            created_by=user_id,
            updated_at=now,
            updated_by=user_id,
        )
        await self.repo.create(file_entity)
        await self.db.commit()
        await self.db.refresh(file_entity)

        return FileUploadResponse(
            file_id=file_entity.id,
            original_name=file_entity.original_name,
            url_path=file_entity.url_path,
            file_size=file_entity.file_size,
            file_ext=file_entity.file_ext,
        )

    async def get_file_path(self, uuid_str: str) -> tuple[str, str, str]:
        file = await self.repo.get_by_uuid(uuid_str)
        if not file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "FILE_NOT_FOUND", "message": "파일을 찾을 수 없습니다."},
            )
        if not os.path.exists(file.local_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "FILE_NOT_FOUND", "message": "파일을 찾을 수 없습니다."},
            )
        return file.local_path, file.original_name, file.mime_type
