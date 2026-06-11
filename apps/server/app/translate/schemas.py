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
    # populate_by_name: service에서 book_id= 키워드로 생성하므로 alias(id)와 필드명 둘 다 허용
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    book_id: str = Field(validation_alias="id")
    title: str
    source_file_url: str | None = None
    created_at: datetime


AdminTranslationStatus = Literal[
    "all",
    "PENDING",
    "OCR_PROCESSING",
    "OCR_COMPLETED",
    "TRANSLATING",
    "COMPLETED",
    "FAILED",
]


class AdminTranslationListRequest(BaseModel):
    page: int = Field(default=1, ge=1, description="페이지 번호", examples=[1])
    size: int = Field(default=10, ge=1, le=100, description="페이지 크기", examples=[10])
    keyword: str | None = Field(
        default=None, max_length=100, description="검색어", examples=["홍길동"]
    )
    status: AdminTranslationStatus = Field(
        default="all", description="번역 상태 필터", examples=["all"]
    )


class AdminTranslationSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    book_id: str = Field(..., description="번역 Book ID", examples=["BOOK_00000001"])
    title: str = Field(..., description="번역 제목", examples=["고문서 번역"])
    owner_name: str = Field(..., description="소유자 성명", examples=["홍길동"])
    owner_is_self: bool = Field(..., description="현재 관리자 본인 소유 여부", examples=[False])
    status: str = Field(..., description="번역 상태", examples=["FAILED"])
    total_pages: int = Field(..., description="전체 페이지 수", examples=[1])
    created_at: datetime = Field(..., description="생성일시")
    latest_run_status: str | None = Field(
        default=None, description="최근 실행 상태", examples=["FAILED"]
    )
    latest_run_error_msg: str | None = Field(
        default=None, description="최근 실행 오류 메시지", examples=["번역 응답 파싱 실패"]
    )
    can_retry: bool = Field(..., description="재시도 가능 여부", examples=[True])


class AdminTranslationPageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    page_no: int = Field(..., description="페이지 번호", examples=[1])
    status: str = Field(..., description="페이지 처리 상태", examples=["FAILED"])
    ocr_text: str | None = Field(default=None, description="OCR 텍스트")
    literal_text: str | None = Field(default=None, description="직역 텍스트")
    interpretive_text: str | None = Field(default=None, description="의역 텍스트")
    has_ocr_text: bool = Field(..., description="OCR 텍스트 존재 여부", examples=[True])
    has_literal_text: bool = Field(..., description="직역 텍스트 존재 여부", examples=[False])
    has_interpretive_text: bool = Field(..., description="의역 텍스트 존재 여부", examples=[False])
    ocr_engine: str | None = Field(default=None, description="OCR 엔진", examples=["GOOGLE_VISION"])
    translator_engine: str | None = Field(
        default=None, description="번역 엔진", examples=["GEMINI"]
    )


class AdminPipelineRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="PipelineRun ID", examples=[1])
    trigger_type: str = Field(..., description="실행 구분", examples=["TRANSLATOR"])
    status: str = Field(..., description="실행 상태", examples=["FAILED"])
    started_at: datetime | None = Field(default=None, description="시작일시")
    completed_at: datetime | None = Field(default=None, description="종료일시")
    duration_ms: int | None = Field(default=None, description="소요 시간(ms)", examples=[60000])
    error_msg: str | None = Field(default=None, description="오류 메시지")


class AdminTranslationDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    book_id: str = Field(..., description="번역 Book ID", examples=["BOOK_00000001"])
    title: str = Field(..., description="번역 제목", examples=["고문서 번역"])
    owner_name: str = Field(..., description="소유자 성명", examples=["홍길동"])
    owner_is_self: bool = Field(..., description="현재 관리자 본인 소유 여부", examples=[False])
    status: str = Field(..., description="번역 상태", examples=["FAILED"])
    book_type: str = Field(..., description="Book 유형", examples=["USER_CREATED"])
    source_type: str = Field(..., description="원본 유형", examples=["IMAGE"])
    total_pages: int = Field(..., description="전체 페이지 수", examples=[1])
    source_file_url: str | None = Field(default=None, description="원본 파일 URL")
    created_at: datetime = Field(..., description="생성일시")
    updated_at: datetime = Field(..., description="수정일시")
    can_retry: bool = Field(..., description="재시도 가능 여부", examples=[True])
    retry_disabled_reason: str | None = Field(default=None, description="재시도 불가 사유")
    pages: list[AdminTranslationPageResponse] = Field(..., description="페이지별 처리 상태")
    pipeline_runs: list[AdminPipelineRunResponse] = Field(..., description="최근 실행 이력")
