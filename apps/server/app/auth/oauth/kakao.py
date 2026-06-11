"""Kakao OAuth 2.0 클라이언트"""

import httpx

from app.config import settings

KAKAO_AUTH_URL = "https://kauth.kakao.com/oauth/authorize"
KAKAO_TOKEN_URL = "https://kauth.kakao.com/oauth/token"
KAKAO_USERINFO_URL = "https://kapi.kakao.com/v2/user/me"


def get_authorization_url(state: str) -> str:
    params = {
        "client_id": settings.kakao_client_id,
        "redirect_uri": settings.kakao_redirect_uri,
        "response_type": "code",
        "scope": "profile_nickname",
        "state": state,
    }
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return f"{KAKAO_AUTH_URL}?{query}"


async def exchange_code(code: str) -> dict[str, object]:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            KAKAO_TOKEN_URL,
            data={
                "client_id": settings.kakao_client_id,
                "client_secret": settings.kakao_client_secret,
                "redirect_uri": settings.kakao_redirect_uri,
                "grant_type": "authorization_code",
                "code": code,
            },
        )
        response.raise_for_status()
        return response.json()  # type: ignore[no-any-return]


async def get_user_info(access_token: str) -> dict[str, object]:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            KAKAO_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        response.raise_for_status()
        data: dict[str, object] = response.json()
        kakao_account: dict[str, object] = data.get("kakao_account", {})  # type: ignore[assignment]
        profile: dict[str, object] = kakao_account.get("profile", {})  # type: ignore[assignment]
        return {
            "id": str(data["id"]),
            "email": kakao_account.get("email"),
            "name": profile.get("nickname"),
            "picture": profile.get("profile_image_url"),
            # email_verified: 필드 부재/파싱 불가 시 False로 안전 처리(계정 연동 금지)
            "email_verified": kakao_account.get("is_email_verified") is True,
        }
