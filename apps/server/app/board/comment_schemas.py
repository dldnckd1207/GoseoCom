"""댓글 Pydantic 스키마"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class CommentResponse(BaseModel):
    id: str = Field(..., description="댓글 ID", examples=["CMT_00000001"])
    post_id: str = Field(..., description="게시글 ID", examples=["POST_00000001"])
    user_id: str | None = Field(
        None, description="작성자 user_id (placeholder 시 null)", examples=["USR_00000001"]
    )
    author_name: str | None = Field(
        None, description="작성자 이름 (placeholder 시 null)", examples=["홍길동"]
    )
    is_ai_gen: bool = Field(..., description="AI 생성 여부", examples=[False])
    is_deleted: bool = Field(..., description="삭제 여부 (true=placeholder)", examples=[False])
    is_filtered: bool = Field(..., description="AI 악성 필터링 여부", examples=[False])
    filter_reason: str | None = Field(None, description="필터링 사유 (FLAGGED일 때만)")
    parent_id: str | None = Field(None, description="대댓글 대상 comment_id")
    depth: int = Field(..., description="0=댓글, 1=대댓글", examples=[0])
    content: str = Field(
        ..., description="내용 (삭제 시 '삭제된 댓글입니다.')", examples=["댓글 내용"]
    )
    created_at: datetime = Field(..., description="작성일시")
    updated_at: datetime = Field(..., description="수정일시")
    replies: list[CommentResponse] = Field(default_factory=list, description="대댓글 목록")

    model_config = {"from_attributes": True}


class CommentListRequest(BaseModel):
    page: int = Field(1, ge=1, description="페이지 번호", examples=[1])
    size: int = Field(20, ge=1, le=100, description="페이지당 항목 수", examples=[20])


class CommentCreateRequest(BaseModel):
    content: str = Field(..., description="댓글 내용")
    parent_id: str | None = Field(None, description="대댓글 대상 comment_id")


class CommentUpdateRequest(BaseModel):
    content: str = Field(..., description="수정할 내용")


class AdminCommentListRequest(BaseModel):
    keyword: str | None = Field(None, description="댓글 내용 or 작성자 이름 검색")
    page: int = Field(1, ge=1, description="페이지 번호", examples=[1])
    size: int = Field(20, ge=1, le=100, description="페이지당 항목 수", examples=[20])


class AdminCommentResponse(BaseModel):
    id: str = Field(..., description="댓글 ID", examples=["CMT_00000001"])
    post_id: str = Field(..., description="게시글 ID", examples=["POST_00000001"])
    post_title: str = Field(..., description="게시글 제목")
    board_name: str = Field(..., description="게시판 이름")
    user_id: str = Field(..., description="작성자 user_id", examples=["USR_00000001"])
    author_name: str = Field(..., description="작성자 이름", examples=["홍길동"])
    content: str = Field(..., description="댓글 내용")
    filter_reason: str | None = Field(None, description="필터링 사유")
    filtered_at: datetime | None = Field(None, description="필터링 시각")
    filter_reviewed_by: str | None = Field(None, description="검토한 관리자 user_id")
    created_at: datetime = Field(..., description="작성일시")
