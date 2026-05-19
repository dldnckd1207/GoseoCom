"""파일 Pydantic 스키마"""

from pydantic import BaseModel, Field


class FileResponse(BaseModel):
    file_id: str = Field(..., description="파일 ID", examples=["FILE_00000001"])
    original_name: str = Field(..., description="원본 파일명", examples=["첨부파일.pdf"])
    url_path: str = Field(..., description="파일 접근 경로", examples=["/files/uuid-here"])
    file_size: int = Field(..., description="파일 크기 (Byte)", examples=[204800])
    file_ext: str = Field(..., description="파일 확장자", examples=["pdf"])

    model_config = {"from_attributes": True}


class FileUploadResponse(BaseModel):
    file_id: str = Field(..., description="발급된 파일 ID", examples=["FILE_00000001"])
    original_name: str = Field(..., description="원본 파일명", examples=["첨부파일.jpg"])
    url_path: str = Field(..., description="파일 접근 경로", examples=["/files/uuid-here"])
    file_size: int = Field(..., description="파일 크기 (Byte)", examples=[204800])
    file_ext: str = Field(..., description="파일 확장자", examples=["jpg"])

    model_config = {"from_attributes": True}
