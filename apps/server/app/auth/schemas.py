from pydantic import BaseModel, Field


class UserMeResponse(BaseModel):
    user_id: str = Field(..., description="사용자 ID", examples=["USR_00000001"])
    email: str = Field(..., description="이메일 주소", examples=["user@example.com"])
    name: str = Field(..., description="표시 이름", examples=["홍길동"])
    profile_image_url: str | None = Field(
        None, description="프로필 이미지 URL", examples=["https://example.com/profile.jpg"]
    )
    user_level: int = Field(
        ..., description="권한 레벨 (0=GUEST, 10=USER, 70=ADMIN, 100=SYSTEM_ADMIN)", examples=[10]
    )


class DevTokenRequest(BaseModel):
    user_id: str = Field(..., description="토큰을 발급할 사용자 ID", examples=["USR_00000001"])


class DevTokenResponse(BaseModel):
    access_token: str = Field(..., description="Access Token (JWT)")
    refresh_token: str = Field(..., description="Refresh Token (JWT)")
