"""게시글 Pydantic 스키마"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.core.files.schemas import FileResponse

AdminPostDeletedStatus = Literal["active", "deleted", "all"]


class PostBookPageData(BaseModel):
    page_no: int
    ocr_text: str | None
    literal_text: str | None
    interpretive_text: str | None

    model_config = {"from_attributes": True}


class PostBookData(BaseModel):
    book_id: str
    title: str
    source_file_url: str | None = None
    summary_text: str | None = None
    keywords: list[dict[str, object]] | None = None
    pages: list[PostBookPageData]

    model_config = {"from_attributes": True}


class PostListRequest(BaseModel):
    board_codes: list[str] = Field(
        ..., description="게시판 코드 목록", min_length=1, examples=[["translation"]]
    )
    keyword: str | None = Field(None, description="제목 검색", examples=[None])
    page: int = Field(1, ge=1, description="페이지 번호", examples=[1])
    size: int = Field(20, ge=1, le=100, description="페이지당 항목 수", examples=[20])


class PostSummaryResponse(BaseModel):
    """목록용 경량 응답"""

    id: str = Field(..., description="게시글 ID", examples=["POST_00000001"])
    board_id: str = Field(..., description="게시판 ID", examples=["BRD_00000001"])
    board_code: str = Field(..., description="게시판 코드", examples=["translation"])
    author_name: str = Field(..., description="작성자 이름 (스냅샷)", examples=["홍길동"])
    is_ai_gen: bool = Field(..., description="AI 생성 여부", examples=[False])
    title: str = Field(..., description="제목", examples=["제목입니다"])
    notice_yn: bool = Field(..., description="공지 여부", examples=[False])
    view_count: int = Field(..., description="조회수", examples=[0])
    comment_count: int = Field(..., description="댓글+대댓글 수 (삭제 제외)", examples=[0])
    created_at: datetime = Field(..., description="작성일시")
    category_id: str | None = Field(None, description="카테고리 ID")
    category_name: str | None = Field(None, description="카테고리명")

    model_config = {"from_attributes": True}


class AdminPostListRequest(BaseModel):
    keyword: str | None = Field(None, description="제목/본문 검색 키워드")
    board_id: str | None = Field(None, description="게시판 ID 필터")
    author_keyword: str | None = Field(None, description="작성자 이름 또는 사용자 ID 검색")
    notice_yn: bool | None = Field(None, description="공지 여부 필터")
    deleted_status: AdminPostDeletedStatus = Field("active", description="삭제 상태 필터")
    page: int = Field(1, ge=1, description="페이지 번호", examples=[1])
    size: int = Field(10, ge=1, le=100, description="페이지당 항목 수", examples=[10])


class AdminPostSummaryResponse(BaseModel):
    id: str = Field(..., description="게시글 ID", examples=["POST_00000001"])
    board_id: str = Field(..., description="게시판 ID", examples=["BRD_00000001"])
    board_code: str = Field(..., description="게시판 코드", examples=["translation"])
    board_name: str = Field(..., description="게시판 이름", examples=["번역"])
    category_id: str | None = Field(None, description="카테고리 ID")
    category_name: str | None = Field(None, description="카테고리명")
    user_id: str = Field(..., description="작성자 user_id", examples=["USR_00000001"])
    author_name: str = Field(..., description="작성자 이름", examples=["홍길동"])
    is_ai_gen: bool = Field(..., description="AI 생성 여부", examples=[False])
    title: str = Field(..., description="제목", examples=["제목입니다"])
    notice_yn: bool = Field(..., description="공지 여부", examples=[False])
    view_count: int = Field(..., description="조회수", examples=[0])
    comment_count: int = Field(..., description="댓글 수", examples=[0])
    auto_reply_status: str = Field(..., description="AI 자동 답변 상태", examples=["PENDING"])
    del_yn: bool = Field(..., description="논리 삭제 여부", examples=[False])
    deleted_at: datetime | None = Field(None, description="삭제일시")
    deleted_by: str | None = Field(None, description="삭제 처리자 ID")
    deleted_by_name: str | None = Field(None, description="삭제 처리자 이름")
    created_at: datetime = Field(..., description="작성일시")
    updated_at: datetime = Field(..., description="수정일시")

    model_config = {"from_attributes": True}


class PostDetailResponse(BaseModel):
    """단건 전체 응답"""

    id: str = Field(..., description="게시글 ID", examples=["POST_00000001"])
    board_id: str = Field(..., description="게시판 ID", examples=["BRD_00000001"])
    board_code: str = Field(..., description="게시판 코드", examples=["translation"])
    user_id: str = Field(..., description="작성자 user_id", examples=["USR_00000001"])
    author_name: str = Field(..., description="작성자 이름 (스냅샷)", examples=["홍길동"])
    is_ai_gen: bool = Field(..., description="AI 생성 여부", examples=[False])
    parent_id: str | None = Field(None, description="답글 대상 post_id")
    depth: int = Field(..., description="0=원글, 1=답글", examples=[0])
    title: str = Field(..., description="제목", examples=["제목입니다"])
    content: str = Field(..., description="본문", examples=["본문 내용입니다."])
    notice_yn: bool = Field(..., description="공지 여부", examples=[False])
    view_count: int = Field(..., description="조회수", examples=[0])
    comment_count: int = Field(..., description="댓글+대댓글 수", examples=[0])
    auto_reply_status: str = Field(..., description="AI 자동 답변 상태", examples=["PENDING"])
    files: list[FileResponse] = Field(default_factory=list, description="첨부파일 목록")
    created_at: datetime = Field(..., description="작성일시")
    updated_at: datetime = Field(..., description="수정일시")
    category_id: str | None = Field(None, description="카테고리 ID")
    category_name: str | None = Field(None, description="카테고리명")
    book: PostBookData | None = Field(None, description="연결된 번역 이력")

    model_config = {"from_attributes": True}


class AdminPostDetailResponse(AdminPostSummaryResponse):
    content: str = Field(..., description="본문", examples=["본문 내용입니다."])
    parent_id: str | None = Field(None, description="답글 대상 post_id")
    depth: int = Field(..., description="0=원글, 1=답글", examples=[0])
    files: list[FileResponse] = Field(default_factory=list, description="첨부파일 목록")
    book: PostBookData | None = Field(None, description="연결된 번역 이력")


class PostCreateRequest(BaseModel):
    board_code: str = Field(..., description="게시판 코드")
    title: str = Field(..., max_length=255, description="제목")
    content: str = Field(..., description="본문")
    notice_yn: bool = Field(False, description="공지 여부 (ADMIN만 true 설정 가능)")
    parent_id: str | None = Field(None, description="답글 대상 post_id")
    file_ids: list[str] = Field(
        default_factory=list, description="선업로드 파일 ID 목록. 중복은 서버에서 제거."
    )
    category_id: str | None = Field(None, description="게시판 카테고리 ID (optional)")
    book_id: str | None = Field(None, description="연결할 번역 이력 ID (optional)")


class PostUpdateRequest(BaseModel):
    title: str | None = Field(None, max_length=255, description="제목")
    content: str | None = Field(None, description="본문")
    notice_yn: bool | None = Field(None, description="공지 여부")
    file_ids: list[str] | None = Field(
        None, description="최종 첨부 목록 (None=변경 안 함, []=전체 제거)"
    )
    book_id: str | None = Field(
        None, description="연결할 번역 이력 ID (None=연결 해제, 미포함=변경 없음)"
    )
    category_id: str | None = Field(None, description="카테고리 ID (None=해제, 미포함=변경 없음)")
