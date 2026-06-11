"""사용자 Pydantic 스키마"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

UserLevelValue = Literal[10, 70, 100]
AdminUserRoleFilter = Literal["all", "user", "admin", "system_admin"]


class AdminUserListRequest(BaseModel):
    keyword: str | None = Field(None, description="이름/이메일 검색 키워드")
    role: AdminUserRoleFilter = Field("all", description="권한 필터")
    use_yn: bool | None = Field(None, description="사용 여부 필터")
    block_yn: bool | None = Field(None, description="차단 여부 필터")
    include_deleted: bool = Field(False, description="탈퇴/삭제 사용자 포함 여부")
    page: int = Field(1, ge=1, description="페이지 번호", examples=[1])
    size: int = Field(10, ge=1, le=100, description="페이지당 항목 수", examples=[10])


class AdminUserUpdateRequest(BaseModel):
    user_level: UserLevelValue | None = Field(None, description="권한 레벨")
    use_yn: bool | None = Field(None, description="사용 여부")
    block_yn: bool | None = Field(None, description="차단 여부")


class AdminUserForceWithdrawRequest(BaseModel):
    left_reason: str = Field(..., min_length=1, max_length=500, description="강제 탈퇴 사유")


class AdminUserListItemResponse(BaseModel):
    id: str = Field(..., description="사용자 ID", examples=["USR_00000001"])
    email: str = Field(..., description="이메일")
    name: str = Field(..., description="이름")
    profile_image_url: str | None = Field(None, description="프로필 이미지 URL")
    user_level: int = Field(..., description="권한 레벨")
    role_label: str = Field(..., description="권한 표시명")
    use_yn: bool = Field(..., description="사용 여부")
    block_yn: bool = Field(..., description="차단 여부")
    joined_at: datetime = Field(..., description="가입일시")
    last_login_at: datetime | None = Field(None, description="마지막 로그인일시")
    left_at: datetime | None = Field(None, description="탈퇴일시")
    del_yn: bool = Field(..., description="삭제 여부")
    is_self: bool = Field(..., description="요청자 본인 여부")


class AdminUserDetailResponse(AdminUserListItemResponse):
    blocked_at: datetime | None = Field(None, description="차단일시")
    blocked_by: str | None = Field(None, description="차단 처리자 ID")
    left_reason: str | None = Field(None, description="탈퇴 사유")
