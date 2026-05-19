"""Auth 라우터 — OAuth 로그인, 토큰 갱신, 로그아웃, 내 정보"""

import secrets
from types import ModuleType
from typing import Annotated, Any

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.oauth import google, kakao
from app.auth.schemas import UserMeResponse
from app.auth.service import AuthService
from app.config import settings
from app.core.common.decorators.require_level import require_level
from app.core.common.enums import AppEnv, UserRole
from app.core.common.response import ApiResponse
from app.db.session import get_db

router = APIRouter(prefix="/auth", tags=["auth"])
users_router = APIRouter(prefix="/api/v1/users", tags=["users"])

_SECURE = settings.app_env == AppEnv.PRODUCTION


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    response.set_cookie(
        "access_token", access_token, max_age=3600, httponly=True, samesite="lax", secure=_SECURE
    )
    response.set_cookie(
        "refresh_token",
        refresh_token,
        max_age=60 * 60 * 24 * 30,
        httponly=True,
        samesite="lax",
        secure=_SECURE,
    )


def _clear_auth_cookies(response: Response) -> None:
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")


async def _handle_oauth_callback(
    code: str,
    state: str,
    oauth_state: str | None,
    provider_name: str,
    provider_module: ModuleType,
    request: Request,
    db: AsyncSession,
) -> RedirectResponse:
    """OAuth 콜백 공통 처리 — state 검증, 토큰 교환, 유저 UPSERT, 쿠키 발급"""
    if not oauth_state or oauth_state != state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_STATE", "message": "유효하지 않은 요청입니다."},
        )

    token_data = await provider_module.exchange_code(code)
    user_info = await provider_module.get_user_info(token_data["access_token"])

    service = AuthService(db)
    access_token, refresh_token = await service.login_or_register(
        provider=provider_name,
        provider_user_id=user_info["id"],
        email=user_info.get("email"),  # TODO(#106): 카카오 비즈앱 전환 후 email 필수화
        name=user_info.get("name") or f"{provider_name.capitalize()}_{str(user_info['id'])[-6:]}",
        profile_image_url=user_info.get("picture"),
        request=request,
    )

    redirect = RedirectResponse(url=settings.app_client_url, status_code=302)
    redirect.delete_cookie("oauth_state")
    _set_auth_cookies(redirect, access_token, refresh_token)
    return redirect


# ---------------------------------------------------------------------------
# 공통 에러 응답 예시 (Swagger responses 재사용)
# ---------------------------------------------------------------------------

_ERR_401_UNAUTHORIZED = {
    "description": "인증 필요",
    "content": {
        "application/json": {
            "examples": {
                "no_token": {
                    "summary": "토큰 없음",
                    "value": {
                        "header": {
                            "success": False,
                            "code": "UNAUTHORIZED",
                            "message": "로그인이 필요합니다.",
                        },
                        "body": {"data": None},
                    },
                },
                "token_expired": {
                    "summary": "토큰 만료",
                    "value": {
                        "header": {
                            "success": False,
                            "code": "TOKEN_EXPIRED",
                            "message": "토큰이 만료되었습니다.",
                        },
                        "body": {"data": None},
                    },
                },
                "invalid_token": {
                    "summary": "유효하지 않은 토큰",
                    "value": {
                        "header": {
                            "success": False,
                            "code": "INVALID_TOKEN",
                            "message": "유효하지 않은 토큰입니다.",
                        },
                        "body": {"data": None},
                    },
                },
            }
        }
    },
}

_ERR_403_FORBIDDEN = {
    "description": "권한 없음",
    "content": {
        "application/json": {
            "examples": {
                "forbidden": {
                    "summary": "권한 부족",
                    "value": {
                        "header": {
                            "success": False,
                            "code": "FORBIDDEN",
                            "message": "접근 권한이 없습니다.",
                        },
                        "body": {"data": None},
                    },
                },
                "account_disabled": {
                    "summary": "비활성 계정",
                    "value": {
                        "header": {
                            "success": False,
                            "code": "ACCOUNT_DISABLED",
                            "message": "비활성화된 계정입니다.",
                        },
                        "body": {"data": None},
                    },
                },
                "account_blocked": {
                    "summary": "차단 계정",
                    "value": {
                        "header": {
                            "success": False,
                            "code": "ACCOUNT_BLOCKED",
                            "message": "이용이 제한된 계정입니다.",
                        },
                        "body": {"data": None},
                    },
                },
            }
        }
    },
}


# ---------------------------------------------------------------------------
# Google OAuth
# ---------------------------------------------------------------------------


@router.get(
    "/google",
    summary="Google OAuth 로그인 시작",
    description="Google 로그인 페이지로 리다이렉트합니다. state 쿠키를 발급하여 CSRF를 방지합니다.",
    tags=["auth"],
)
async def google_login() -> RedirectResponse:
    state = secrets.token_urlsafe(32)
    response = RedirectResponse(url=google.get_authorization_url(state), status_code=302)
    response.set_cookie("oauth_state", state, max_age=600, httponly=True, samesite="lax")
    return response


@router.get(
    "/google/callback",
    summary="Google OAuth 콜백",
    description="Google 인증 완료 후 호출되는 콜백 엔드포인트. state 검증 후 JWT 쿠키를 발급하고 클라이언트로 리다이렉트합니다.",
    tags=["auth"],
)
async def google_callback(
    code: str,
    state: str,
    request: Request,
    oauth_state: Annotated[str | None, Cookie()] = None,
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    return await _handle_oauth_callback(code, state, oauth_state, "GOOGLE", google, request, db)


# ---------------------------------------------------------------------------
# Kakao OAuth
# ---------------------------------------------------------------------------


@router.get(
    "/kakao",
    summary="Kakao OAuth 로그인 시작",
    description="Kakao 로그인 페이지로 리다이렉트합니다. state 쿠키를 발급하여 CSRF를 방지합니다.",
    tags=["auth"],
)
async def kakao_login() -> RedirectResponse:
    state = secrets.token_urlsafe(32)
    response = RedirectResponse(url=kakao.get_authorization_url(state), status_code=302)
    response.set_cookie("oauth_state", state, max_age=600, httponly=True, samesite="lax")
    return response


@router.get(
    "/kakao/callback",
    summary="Kakao OAuth 콜백",
    description="Kakao 인증 완료 후 호출되는 콜백 엔드포인트. state 검증 후 JWT 쿠키를 발급하고 클라이언트로 리다이렉트합니다.",
    tags=["auth"],
)
async def kakao_callback(
    code: str,
    state: str,
    request: Request,
    oauth_state: Annotated[str | None, Cookie()] = None,
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    return await _handle_oauth_callback(code, state, oauth_state, "KAKAO", kakao, request, db)


# ---------------------------------------------------------------------------
# Token 갱신 / 로그아웃
# ---------------------------------------------------------------------------


@router.post(
    "/refresh",
    summary="Access Token 갱신",
    description=(
        "Refresh Token 쿠키를 사용하여 새로운 Access/Refresh Token을 발급합니다.\n\n"
        "- Refresh Token Rotation: 사용 시 기존 토큰 무효화 + 새 토큰 발급\n"
        "- 무효화된 토큰 재사용 감지 시 해당 사용자의 전체 세션 무효화 (탈취 감지)\n"
        "- Grace Period: 30초 이내 재사용은 허용 (네트워크 지연 대응)"
    ),
    response_model=ApiResponse[None],
    responses={401: _ERR_401_UNAUTHORIZED},
    tags=["auth"],
)
async def refresh(
    request: Request,
    response: Response,
    refresh_token: Annotated[str | None, Cookie()] = None,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[None]:
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "UNAUTHORIZED", "message": "Refresh Token이 없습니다."},
        )
    service = AuthService(db)
    new_access, new_refresh = await service.refresh(refresh_token, request)
    _set_auth_cookies(response, new_access, new_refresh)
    return ApiResponse.success(None, message="토큰 갱신 성공")


@router.post(
    "/logout",
    summary="로그아웃",
    description="Refresh Token을 무효화하고 인증 쿠키를 삭제합니다. 토큰이 없어도 정상 처리됩니다.",
    response_model=ApiResponse[None],
    tags=["auth"],
)
async def logout(
    response: Response,
    refresh_token: Annotated[str | None, Cookie()] = None,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[None]:
    service = AuthService(db)
    await service.logout(refresh_token)
    _clear_auth_cookies(response)
    return ApiResponse.deleted("로그아웃 성공")


# ---------------------------------------------------------------------------
# 내 정보 조회
# ---------------------------------------------------------------------------


@users_router.get(
    "/me",
    summary="내 정보 조회",
    description="로그인한 사용자의 프로필 정보를 반환합니다. Access Token 쿠키가 필요합니다.",
    response_model=ApiResponse[UserMeResponse],
    responses={
        401: _ERR_401_UNAUTHORIZED,
        403: _ERR_403_FORBIDDEN,
        404: {
            "description": "사용자 없음",
            "content": {
                "application/json": {
                    "example": {
                        "header": {
                            "success": False,
                            "code": "USER_NOT_FOUND",
                            "message": "사용자를 찾을 수 없습니다.",
                        },
                        "body": {"data": None},
                    }
                }
            },
        },
    },
    tags=["users"],
)
async def get_me(
    payload: dict[str, Any] = require_level(UserRole.USER),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[UserMeResponse]:
    from app.auth.repository import AuthRepository

    repo = AuthRepository(db)
    user = await repo.get_user_by_id(payload["sub"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "USER_NOT_FOUND", "message": "사용자를 찾을 수 없습니다."},
        )
    return ApiResponse.success(
        UserMeResponse(
            user_id=user.id,
            email=user.email,
            name=user.name,
            profile_image_url=user.profile_image_url,
            user_level=user.user_level,
        )
    )
