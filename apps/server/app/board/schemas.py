"""게시판 Pydantic 스키마"""

from pydantic import BaseModel, Field, field_validator

from app.core.common.enums import BoardType

# ---------------------------------------------------------------------------
# 클라이언트 — 요청
# ---------------------------------------------------------------------------


class BoardListRequest(BaseModel):
    board_group: str | None = Field(
        None, description="게시판 그룹 필터 (예: 'community')", examples=["community"]
    )
    page: int = Field(1, ge=1, description="페이지 번호", examples=[1])
    size: int = Field(20, ge=1, le=100, description="페이지당 항목 수", examples=[20])


# ---------------------------------------------------------------------------
# 클라이언트 — 응답
# ---------------------------------------------------------------------------


class BoardCategoryResponse(BaseModel):
    """게시판 카테고리 응답"""

    id: str = Field(..., description="카테고리 ID", examples=["BCAT_00000001"])
    category_name: str = Field(..., description="카테고리 이름", examples=["조선"])
    sort_order: int = Field(..., description="정렬 순서", examples=[3])

    model_config = {"from_attributes": True}


class BoardSummaryResponse(BaseModel):
    """목록 탭 렌더링용 경량 응답"""

    id: str = Field(..., description="게시판 ID", examples=["BRD_00000001"])
    board_code: str = Field(..., description="게시판 코드 (slug)", examples=["translation"])
    board_name: str = Field(..., description="게시판 이름", examples=["번역"])
    board_type: str = Field(..., description="게시판 타입 (LIST | IMAGE | QNA)", examples=["LIST"])
    guest_read_yn: bool = Field(..., description="비회원 읽기 허용 여부", examples=[True])
    write_yn: bool = Field(..., description="로그인 사용자 쓰기 허용", examples=[True])
    board_group: str | None = Field(
        None, description="게시판 그룹 (예: 'community')", examples=["community"]
    )
    sort_order: int = Field(..., description="노출 순서", examples=[0])
    use_yn: bool = Field(..., description="활성 여부", examples=[True])
    attach_yn: bool = Field(..., description="첨부파일 허용 여부", examples=[True])
    attach_ext: str | None = Field(
        None, description="허용 확장자 CSV (예: 'jpg,png')", examples=["jpg,jpeg,png"]
    )
    attach_size: int = Field(..., description="최대 첨부 크기 (KB)", examples=[10240])

    model_config = {"from_attributes": True}


class BoardDetailResponse(BaseModel):
    """게시판 진입 시 전체 설정 응답"""

    id: str = Field(..., description="게시판 ID", examples=["BRD_00000001"])
    board_code: str = Field(..., description="게시판 코드 (slug)", examples=["translation"])
    board_name: str = Field(..., description="게시판 이름", examples=["번역"])
    board_desc: str | None = Field(
        None, description="게시판 설명", examples=["번역 관련 게시판입니다."]
    )
    board_type: str = Field(..., description="게시판 타입 (LIST | IMAGE | QNA)", examples=["LIST"])
    read_yn: bool = Field(..., description="로그인 사용자 읽기 허용", examples=[True])
    guest_read_yn: bool = Field(..., description="비회원 읽기 허용", examples=[True])
    write_yn: bool = Field(..., description="로그인 사용자 쓰기 허용", examples=[True])
    guest_write_yn: bool = Field(..., description="비회원 쓰기 허용", examples=[False])
    notice_yn: bool = Field(..., description="공지 기능 허용", examples=[True])
    reply_yn: bool = Field(..., description="답글(대댓글) 허용", examples=[False])
    comment_yn: bool = Field(..., description="댓글 허용", examples=[True])
    attach_yn: bool = Field(..., description="첨부파일 허용", examples=[True])
    attach_ext: str | None = Field(None, description="허용 확장자 (CSV)", examples=["jpg,png,pdf"])
    attach_size: int = Field(..., description="최대 첨부 크기 (KB)", examples=[10240])
    attach_count: int = Field(..., description="최대 첨부 개수", examples=[5])
    list_count: int = Field(..., description="페이지당 목록 수", examples=[20])
    auto_reply_enabled: bool = Field(..., description="AI 자동 답변 활성화", examples=[False])
    sort_order: int = Field(..., description="노출 순서", examples=[0])
    use_yn: bool = Field(..., description="활성 여부", examples=[True])

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# 관리자 — 요청
# ---------------------------------------------------------------------------


class AdminBoardCreateRequest(BaseModel):
    board_code: str = Field(..., max_length=50, description="URL slug (UNIQUE)", examples=["free"])
    board_name: str = Field(..., max_length=100, description="게시판 이름", examples=["자유게시판"])
    board_desc: str | None = Field(None, max_length=500, description="게시판 설명")
    board_group: str | None = Field(
        None, max_length=50, description="게시판 그룹 (예: 'community')", examples=["community"]
    )
    board_type: str = Field(
        "LIST", description="게시판 타입 (LIST | IMAGE | QNA)", examples=["LIST"]
    )
    read_yn: bool = Field(True, description="로그인 사용자 읽기 허용")
    guest_read_yn: bool = Field(True, description="비회원 읽기 허용")
    write_yn: bool = Field(True, description="로그인 사용자 쓰기 허용")
    guest_write_yn: bool = Field(False, description="비회원 쓰기 허용")
    notice_yn: bool = Field(True, description="공지 기능 허용")
    reply_yn: bool = Field(False, description="답글 허용")
    comment_yn: bool = Field(False, description="댓글 허용")
    category_yn: bool = Field(False, description="카테고리 허용")
    attach_yn: bool = Field(True, description="첨부파일 허용")
    attach_ext: str | None = Field(
        None, max_length=255, description="허용 확장자 CSV", examples=["jpg,png,pdf"]
    )
    attach_size: int = Field(10240, ge=0, description="최대 첨부 크기 (KB)")
    attach_count: int = Field(5, ge=0, description="최대 첨부 개수")
    list_count: int = Field(20, ge=1, le=100, description="페이지당 목록 수")
    auto_reply_enabled: bool = Field(False, description="AI 자동 답변 활성화")
    auto_reply_delay_min: int = Field(5, ge=0, description="자동 답변 딜레이 (분)")
    sort_order: int = Field(0, description="노출 순서")

    @field_validator("board_type")
    @classmethod
    def validate_board_type(cls, v: str) -> str:
        valid = {t.value for t in BoardType}
        if v not in valid:
            raise ValueError(f"board_type은 {valid} 중 하나여야 합니다.")
        return v


class AdminBoardUpdateRequest(BaseModel):
    board_name: str | None = Field(None, max_length=100, description="게시판 이름")
    board_desc: str | None = Field(None, max_length=500, description="게시판 설명")
    board_group: str | None = Field(
        None, max_length=50, description="게시판 그룹 (예: 'community')"
    )
    board_type: str | None = Field(None, description="게시판 타입 (LIST | IMAGE | QNA)")
    read_yn: bool | None = None
    guest_read_yn: bool | None = None
    write_yn: bool | None = None
    guest_write_yn: bool | None = None
    notice_yn: bool | None = None
    reply_yn: bool | None = None
    comment_yn: bool | None = None
    category_yn: bool | None = None
    attach_yn: bool | None = None
    attach_ext: str | None = None
    attach_size: int | None = Field(None, ge=0)
    attach_count: int | None = Field(None, ge=0)
    list_count: int | None = Field(None, ge=1, le=100)
    auto_reply_enabled: bool | None = None
    auto_reply_delay_min: int | None = Field(None, ge=0)
    sort_order: int | None = None
    use_yn: bool | None = None

    @field_validator("board_type")
    @classmethod
    def validate_board_type(cls, v: str | None) -> str | None:
        if v is None:
            return v
        valid = {t.value for t in BoardType}
        if v not in valid:
            raise ValueError(f"board_type은 {valid} 중 하나여야 합니다.")
        return v


class AdminBoardListRequest(BaseModel):
    keyword: str | None = Field(None, description="board_name 검색 키워드")
    use_yn: bool | None = Field(None, description="활성 여부 필터 (null=전체)")
    page: int = Field(1, ge=1, description="페이지 번호", examples=[1])
    size: int = Field(20, ge=1, le=100, description="페이지당 항목 수", examples=[20])


class AdminBoardCategoryCreateRequest(BaseModel):
    category_name: str = Field(..., max_length=100, description="카테고리 이름")
    sort_order: int = Field(0, description="정렬 순서")
    use_yn: bool = Field(True, description="사용 여부")


class AdminBoardCategoryUpdateRequest(BaseModel):
    category_name: str | None = Field(None, max_length=100, description="카테고리 이름")
    sort_order: int | None = Field(None, description="정렬 순서")
    use_yn: bool | None = Field(None, description="사용 여부")


# ---------------------------------------------------------------------------
# 관리자 — 응답
# ---------------------------------------------------------------------------


class AdminBoardResponse(BaseModel):
    """관리자용 전체 설정 응답"""

    id: str = Field(..., description="게시판 ID", examples=["BRD_00000001"])
    board_code: str = Field(..., description="게시판 코드 (slug)", examples=["translation"])
    board_name: str = Field(..., description="게시판 이름", examples=["번역"])
    board_desc: str | None = Field(None, description="게시판 설명")
    board_group: str | None = Field(
        None, description="게시판 그룹 (예: 'community')", examples=["community"]
    )
    board_type: str = Field(..., description="게시판 타입", examples=["LIST"])
    read_yn: bool = Field(..., description="로그인 사용자 읽기 허용")
    guest_read_yn: bool = Field(..., description="비회원 읽기 허용")
    write_yn: bool = Field(..., description="로그인 사용자 쓰기 허용")
    guest_write_yn: bool = Field(..., description="비회원 쓰기 허용")
    notice_yn: bool = Field(..., description="공지 기능 허용")
    reply_yn: bool = Field(..., description="답글 허용")
    comment_yn: bool = Field(..., description="댓글 허용")
    secret_yn: bool = Field(..., description="비밀글 허용 (Phase 3)")
    like_yn: bool = Field(..., description="좋아요 허용 (Phase 3)")
    category_yn: bool = Field(..., description="카테고리 허용 (Phase 3)")
    attach_yn: bool = Field(..., description="첨부파일 허용")
    attach_ext: str | None = Field(None, description="허용 확장자 CSV", examples=["jpg,png,pdf"])
    attach_size: int = Field(..., description="최대 첨부 크기 (KB)", examples=[10240])
    attach_count: int = Field(..., description="최대 첨부 개수", examples=[5])
    list_count: int = Field(..., description="페이지당 목록 수", examples=[20])
    auto_reply_enabled: bool = Field(..., description="AI 자동 답변 활성화")
    auto_reply_delay_min: int = Field(..., description="자동 답변 딜레이 (분)", examples=[5])
    pipeline_enabled: bool = Field(..., description="파이프라인 활성화 (Phase 2)")
    sort_order: int = Field(..., description="노출 순서", examples=[0])
    use_yn: bool = Field(..., description="활성 여부")
    del_yn: bool = Field(..., description="삭제 여부")

    model_config = {"from_attributes": True}


class AdminBoardCategoryResponse(BaseModel):
    """관리자용 게시판 카테고리 응답"""

    id: str = Field(..., description="카테고리 ID", examples=["BCAT_00000001"])
    board_id: str = Field(..., description="게시판 ID", examples=["BRD_00000001"])
    category_name: str = Field(..., description="카테고리 이름", examples=["조선"])
    sort_order: int = Field(..., description="정렬 순서", examples=[3])
    use_yn: bool = Field(..., description="사용 여부")
    del_yn: bool = Field(..., description="삭제 여부")

    model_config = {"from_attributes": True}
