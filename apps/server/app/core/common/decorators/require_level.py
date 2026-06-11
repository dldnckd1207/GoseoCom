"""권한 레벨 체크 데코레이터"""

from typing import Annotated, Any, cast

import jwt
from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.common.enums import UserRole
from app.core.security import decode_token
from app.core.user.models import User
from app.db.session import get_db


def require_level(min_level: UserRole) -> Any:
    """
    최소 권한 레벨을 체크하는 FastAPI Dependency.

    사용법:
        @router.post("/list", dependencies=[require_level(UserRole.GUEST)])
        payload: dict[str, Any] = require_level(UserRole.USER)
    """

    async def _check(
        access_token: Annotated[str | None, Cookie()] = None,
        db: AsyncSession = Depends(get_db),
    ) -> dict[str, Any]:
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

        # 차단/비활성 즉시 반영(점검보고서 #8): 토큰 클레임 대신 DB의 현재 상태를 재확인한다.
        # 관리자가 차단/비활성하면 기존 Access Token도 다음 요청부터 즉시 거부된다.
        user = (
            await db.execute(select(User).where(User.id == user_id, User.del_yn.is_(False)))
        ).scalar_one_or_none()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "INVALID_TOKEN", "message": "유효하지 않은 토큰입니다."},
            )
        if not user.use_yn:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "ACCOUNT_DISABLED", "message": "비활성화된 계정입니다."},
            )
        # 차단 계정: 로그인은 허용되나 USER 이상 서비스 이용 제한 (UBR-05)
        if user.block_yn and min_level >= UserRole.USER:
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
