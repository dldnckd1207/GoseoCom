"""공통 API 응답 형식 — { header, body: { data } }"""

from pydantic import BaseModel, Field


class ResponseHeader(BaseModel):
    success: bool = Field(..., description="성공 여부", examples=[True])
    code: str = Field(
        ...,
        description="응답 코드 (SUCCESS / CREATED / UPDATED / DELETED / 에러코드)",
        examples=["SUCCESS"],
    )
    message: str = Field(
        ..., description="응답 메시지", examples=["요청이 성공적으로 처리되었습니다."]
    )


class ResponseBody[T](BaseModel):
    data: T | None = Field(None, description="응답 데이터 (에러 시 null)")


class ApiResponse[T](BaseModel):
    header: ResponseHeader
    body: ResponseBody[T]

    @classmethod
    def success(
        cls,
        data: T,
        code: str = "SUCCESS",
        message: str = "요청이 성공적으로 처리되었습니다.",
    ) -> "ApiResponse[T]":
        return cls(
            header=ResponseHeader(success=True, code=code, message=message),
            body=ResponseBody(data=data),
        )

    @classmethod
    def created(
        cls,
        data: T,
        message: str = "생성되었습니다.",
    ) -> "ApiResponse[T]":
        return cls.success(data, code="CREATED", message=message)

    @classmethod
    def updated(
        cls,
        data: T,
        message: str = "수정되었습니다.",
    ) -> "ApiResponse[T]":
        return cls.success(data, code="UPDATED", message=message)

    @classmethod
    def deleted(
        cls,
        message: str = "삭제되었습니다.",
    ) -> "ApiResponse[None]":
        return ApiResponse(
            header=ResponseHeader(success=True, code="DELETED", message=message),
            body=ResponseBody(data=None),
        )

    @classmethod
    def error(
        cls,
        code: str,
        message: str,
    ) -> "ApiResponse[None]":
        return ApiResponse(
            header=ResponseHeader(success=False, code=code, message=message),
            body=ResponseBody(data=None),
        )


class PageData[T](BaseModel):
    """목록/페이징 응답 data 구조"""

    items: list[T]
    total: int
    page: int
    size: int
