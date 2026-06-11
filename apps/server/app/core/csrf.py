"""double-submit CSRF 보호 미들웨어 (점검보고서 #7 / D-4=(b))

비-httpOnly ``csrf_token`` 쿠키를 발급하고, 상태변경 요청(POST/PUT/DELETE/PATCH)에서
``X-CSRF-Token`` 헤더가 쿠키값과 일치하는지 검증한다.

- ``/auth/*`` 는 자체 보호(OAuth state, Refresh Token Rotation/재사용 감지)가 있어 제외한다.
- 토큰을 보유하지 않은 클라이언트에는 응답에 ``csrf_token`` 쿠키를 시드해 다음 요청부터
  더블 서브밋이 성립하도록 한다.
- 개발 환경(HTTP, 교차 출처) 편의를 위해 ``enabled=False`` 면 통과만 한다.
"""

import secrets
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.config import settings
from app.core.common.enums import AppEnv

CSRF_COOKIE_NAME = "csrf_token"
CSRF_HEADER_NAME = "X-CSRF-Token"
_PROTECTED_METHODS = frozenset({"POST", "PUT", "DELETE", "PATCH"})
# 자체 인증/보호 메커니즘이 있는 경로는 CSRF 검증 제외
_EXEMPT_PREFIXES = ("/auth/",)


def _is_exempt(path: str) -> bool:
    return path.startswith(_EXEMPT_PREFIXES)


class CSRFMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: Callable[..., Awaitable[None]], *, enabled: bool = True) -> None:
        super().__init__(app)
        self.enabled = enabled

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if not self.enabled:
            return await call_next(request)

        if request.method in _PROTECTED_METHODS and not _is_exempt(request.url.path):
            cookie_token = request.cookies.get(CSRF_COOKIE_NAME)
            header_token = request.headers.get(CSRF_HEADER_NAME)
            if (
                not cookie_token
                or not header_token
                or not secrets.compare_digest(cookie_token, header_token)
            ):
                return JSONResponse(
                    status_code=403,
                    content={
                        "header": {
                            "success": False,
                            "code": "CSRF_FAILED",
                            "message": "CSRF 검증에 실패했습니다.",
                        },
                        "body": {"data": None},
                    },
                )

        response = await call_next(request)

        # 토큰 미보유 클라이언트에 시드 (non-httpOnly: 프론트가 읽어 헤더로 재전송)
        if CSRF_COOKIE_NAME not in request.cookies:
            response.set_cookie(
                CSRF_COOKIE_NAME,
                secrets.token_urlsafe(32),
                httponly=False,
                samesite="lax",
                secure=settings.app_env != AppEnv.DEVELOPMENT,
            )
        return response
