"""파일 서빙/업로드 라우터"""

import re
from typing import Any
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.common.decorators.require_level import require_level
from app.core.common.enums import UserRole
from app.core.common.response import ApiResponse
from app.core.files.schemas import FileUploadResponse
from app.core.files.service import FileService
from app.db.session import get_db

router = APIRouter(tags=["files"])

_MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB

# 인라인 렌더를 허용할 안전한 MIME (그 외에는 강제 다운로드 — 저장형 XSS 차단, 점검보고서 #4)
_INLINE_SAFE_MIME = {
    "image/png",
    "image/jpeg",
    "image/gif",
    "image/webp",
    "application/pdf",
}


def _sanitize_filename(name: str) -> str:
    """Content-Disposition 헤더 주입 방지 — 개행/제어문자 제거 (점검보고서 #10)."""
    cleaned = re.sub(r"[\r\n\x00-\x1f\x7f]", "", name).strip()
    return cleaned or "download"


@router.post(
    "/api/v1/uploads",
    summary="일반 파일 업로드",
    description="board context 없는 범용 파일 업로드입니다. 번역기 등에서 사용합니다.",
    response_model=ApiResponse[FileUploadResponse],
    status_code=status.HTTP_201_CREATED,
)
async def upload_file(
    file: UploadFile,
    payload: dict[str, Any] = require_level(UserRole.USER),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[FileUploadResponse]:
    content = await file.read()
    if len(content) > _MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "FILE_SIZE_EXCEEDED",
                "message": "파일 크기는 10MB를 초과할 수 없습니다.",
            },
        )

    service = FileService(db)
    data = await service.upload(file, payload["sub"], content=content)
    return ApiResponse.created(data)


@router.get(
    "/files/{uuid}",
    summary="파일 조회/다운로드",
    description="UUID로 파일을 조회합니다. `?download=true` 시 다운로드 헤더 추가.",
)
async def serve_file(
    uuid: str,
    download: bool = False,
    db: AsyncSession = Depends(get_db),
) -> FileResponse:
    service = FileService(db)
    local_path, original_name, mime_type = await service.get_file_path(uuid)

    # MIME 스니핑 차단 + 안전 화이트리스트 외에는 강제 다운로드 (저장형 XSS 차단)
    safe_name = quote(_sanitize_filename(original_name))
    disposition = "inline" if (not download and mime_type in _INLINE_SAFE_MIME) else "attachment"
    headers = {
        "X-Content-Type-Options": "nosniff",
        "Content-Disposition": f"{disposition}; filename*=UTF-8''{safe_name}",
    }

    return FileResponse(
        path=local_path,
        media_type=mime_type,
        headers=headers,
    )
