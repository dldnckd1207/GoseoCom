"""개발용 라우터 — dev 환경에서만 main.py에 등록됨"""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.repository import AuthRepository
from app.auth.router import _set_auth_cookies
from app.auth.schemas import DevTokenRequest, DevTokenResponse
from app.core.security import create_access_token, create_refresh_token_jwt
from app.db.session import get_db

dev_router = APIRouter(prefix="/auth/dev", tags=["dev"])


@dev_router.post("/token", response_model=DevTokenResponse)
async def dev_token(
    body: DevTokenRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> DevTokenResponse:
    """
    개발용 임시 토큰 발급.
    OAuth 없이 user_id만으로 토큰 발급 — Swagger/Postman 테스트용.
    """
    repo = AuthRepository(db)
    user = await repo.get_user_by_id(body.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "USER_NOT_FOUND", "message": "유저를 찾을 수 없습니다."},
        )

    access_token = create_access_token(user.id, user.user_level, user_name=user.name)
    refresh_token = create_refresh_token_jwt(user.id)

    _set_auth_cookies(response, access_token, refresh_token)

    return DevTokenResponse(access_token=access_token, refresh_token=refresh_token)
