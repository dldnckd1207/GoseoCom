from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

BookStatus = Literal[
    "PENDING", "OCR_PROCESSING", "OCR_COMPLETED", "TRANSLATING", "COMPLETED", "FAILED"
]


class TranslateStartRequest(BaseModel):
    file_id: str


class TranslateStartResponse(BaseModel):
    book_id: str
    status: str


class OcrStartRequest(BaseModel):
    file_id: str


class OcrStartResponse(BaseModel):
    book_id: str
    status: str


class TranslateTextRequest(BaseModel):
    text: str
    book_id: str | None = None


class BookTitleUpdateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)


class PageEditRequest(BaseModel):
    ocr_text: str | None = None
    literal_text: str
    interpretive_text: str


class PageEditResponse(BaseModel):
    version: int


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
    summary_text: str | None = None
    keywords: list[dict[str, object]] | None = None
    pages: list[BookPageResponse]


class BookListRequest(BaseModel):
    page: int = Field(default=1, ge=1)
    size: int = Field(default=10, ge=1, le=100)
    status: BookStatus | None = None
    is_favorite: bool | None = None
    q: str | None = Field(default=None, max_length=100)


class BookListItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    book_id: str = Field(validation_alias="id")
    title: str
    status: str
    is_favorite: bool
    created_at: datetime


class BookFavoriteResponse(BaseModel):
    book_id: str
    is_favorite: bool


class BookPublicListRequest(BaseModel):
    page: int = Field(default=1, ge=1)
    size: int = Field(default=12, ge=1, le=100)
    q: str | None = Field(default=None, max_length=100)
    bm: bool | None = None


class BookPublicListItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    book_id: str = Field(validation_alias="id")
    title: str
    created_at: datetime
    source_file_url: str | None = None
    owner_user_id: str = ""
    owner_name: str = ""
    is_bookmarked: bool = False


class BookBookmarkResponse(BaseModel):
    book_id: str
    is_bookmarked: bool


class BookDropdownItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    book_id: str = Field(validation_alias="id")
    title: str
    source_file_url: str | None = None
    created_at: datetime
