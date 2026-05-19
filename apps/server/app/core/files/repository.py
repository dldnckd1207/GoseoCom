"""파일 Repository — DB 쿼리"""

from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.files.models import File, FileMap


class FileRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, file_id: str) -> File | None:
        result = await self.db.execute(
            select(File).where(File.id == file_id, File.del_yn.is_(False))
        )
        return result.scalar_one_or_none()

    async def get_by_uuid(self, uuid: str) -> File | None:
        result = await self.db.execute(
            select(File).where(File.uuid == uuid, File.del_yn.is_(False))
        )
        return result.scalar_one_or_none()

    async def get_by_ids(self, file_ids: list[str]) -> list[File]:
        if not file_ids:
            return []
        result = await self.db.execute(
            select(File).where(File.id.in_(file_ids), File.del_yn.is_(False))
        )
        files = {f.id: f for f in result.scalars().all()}
        return [files[fid] for fid in file_ids if fid in files]

    async def create(self, file: File) -> File:
        self.db.add(file)
        await self.db.flush()
        return file


class FileMapRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_by_target(self, target_type: str, target_id: str) -> list[FileMap]:
        result = await self.db.execute(
            select(FileMap)
            .where(
                FileMap.target_type == target_type,
                FileMap.target_id == target_id,
                FileMap.del_yn.is_(False),
            )
            .order_by(FileMap.sort_order.asc())
        )
        return list(result.scalars().all())

    async def soft_delete_all_by_target(
        self, target_type: str, target_id: str, deleted_by: str
    ) -> None:
        now = datetime.now(UTC)
        await self.db.execute(
            update(FileMap)
            .where(
                FileMap.target_type == target_type,
                FileMap.target_id == target_id,
                FileMap.del_yn.is_(False),
            )
            .values(del_yn=True, deleted_at=now, deleted_by=deleted_by)
        )

    async def upsert(
        self,
        file_id: str,
        target_type: str,
        target_id: str,
        created_by: str,
        file_group: str = "attachment",
        sort_order: int = 0,
    ) -> None:
        result = await self.db.execute(
            select(FileMap).where(
                FileMap.file_id == file_id,
                FileMap.target_type == target_type,
                FileMap.target_id == target_id,
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            now = datetime.now(UTC)
            existing.del_yn = False
            existing.deleted_at = None
            existing.deleted_by = None
            existing.sort_order = sort_order
            existing.updated_at = now
            existing.updated_by = created_by
        else:
            from app.core.common.id_generator import next_id

            now = datetime.now(UTC)
            file_map = FileMap(
                id=await next_id("FMAP_", self.db),
                file_id=file_id,
                target_type=target_type,
                target_id=target_id,
                file_group=file_group,
                sort_order=sort_order,
                created_at=now,
                created_by=created_by,
                updated_at=now,
                updated_by=created_by,
            )
            self.db.add(file_map)
