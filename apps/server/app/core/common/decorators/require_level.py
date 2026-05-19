"""권한 레벨 체크 데코레이터"""

from typing import Annotated, Any, cast

import jwt
from fastapi import Cookie, Depends, HTTPException, status

from app.core.common.enums import UserRole
from app.core.security import decode_token


def require_level(min_level: UserRole) -> Any:
    """
    최소 권한 레벨을 체크하는 FastAPI Dependency.

    사용법:
        @router.post("/list", dependencies=[require_level(UserRole.GUEST)])
        payload: dict[str, Any] = require_level(UserRole.USER)
    """

    async def _check(access_token: Annotated[str | None, Cookie()] = None) -> dict[str, Any]:
        if min_level == UserRole.GUEST:
            if not access_token:
                return {}
            try:
                return decode_token(access_token)
            except jwt.PyJWTError:
                return {}

        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "UNAUTHORIZED", "message": "로그인이 필요합니다."},
            )
        try:
            payload = decode_token(access_token)
        except jwt.ExpiredSignatureError as err:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "TOKEN_EXPIRED", "message": "토큰이 만료되었습니다."},
            ) from err
        except jwt.PyJWTError as err:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "INVALID_TOKEN", "message": "유효하지 않은 토큰입니다."},
            ) from err

        user_id: str = str(payload.get("sub", ""))
        if user_id == "USR_00000000":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "FORBIDDEN", "message": "접근 권한이 없습니다."},
            )

        # 차단 계정: 로그인은 허용되나 USER 이상 서비스 이용 제한 (UBR-05)
        if payload.get("blocked") and min_level >= UserRole.USER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "ACCOUNT_BLOCKED", "message": "이용이 제한된 계정입니다."},
            )

        user_level: int = cast(int, payload.get("level", 0))
        if user_level < min_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "FORBIDDEN", "message": "접근 권한이 없습니다."},
            )

        return payload

    return Depends(_check)
