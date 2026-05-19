from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

BookStatus = Literal["PENDING", "OCR_PROCESSING", "TRANSLATING", "COMPLETED", "FAILED"]


class TranslateStartRequest(BaseModel):
    file_id: str


class TranslateStartResponse(BaseModel):
    book_id: str
    status: str


class BookPageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    page_no: int
    ocr_text: str | None
    literal_text: str | None
    interpretive_text: str | None
    ocr_engine: str | None
    translator_engine: str | None
    status: str  # PENDING | COMPLETED | NO_TEXT | FAILED


class BookResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    book_id: str = Field(validation_alias="id")
    title: str
    status: str
    total_pages: int
    source_file_url: str | None = None
    pages: list[BookPageResponse]


class BookListRequest(BaseModel):
    page: int = Field(default=1, ge=1)
    size: int = Field(default=10, ge=1, le=100)
    status: BookStatus | None = None


class BookListItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    book_id: str = Field(validation_alias="id")
    title: str
    status: str
    created_at: datetime
