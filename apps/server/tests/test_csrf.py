"""double-submit CSRF 미들웨어 테스트 (점검보고서 #7)"""

from collections.abc import Awaitable, Callable

import pytest
from starlette.requests import Request
from starlette.responses import Response

from app.core.csrf import CSRF_COOKIE_NAME, CSRF_HEADER_NAME, CSRFMiddleware


def _make_request(
    method: str,
    path: str,
    headers: dict[str, str] | None = None,
    cookies: dict[str, str] | None = None,
) -> Request:
    raw_headers: list[tuple[bytes, bytes]] = [
        (k.lower().encode(), v.encode()) for k, v in (headers or {}).items()
    ]
    if cookies:
        cookie_str = "; ".join(f"{k}={v}" for k, v in cookies.items())
        raw_headers.append((b"cookie", cookie_str.encode()))
    return Request(
        {
            "type": "http",
            "method": method,
            "path": path,
            "headers": raw_headers,
            "query_string": b"",
        }
    )


async def _dummy_app(scope: object, receive: object, send: object) -> None:  # pragma: no cover
    return None


def _mw(enabled: bool = True) -> CSRFMiddleware:
    return CSRFMiddleware(_dummy_app, enabled=enabled)


def _ok() -> Callable[[Request], Awaitable[Response]]:
    async def call_next(_request: Request) -> Response:
        return Response("ok", status_code=200)

    return call_next


@pytest.mark.asyncio
async def test_disabled_passes_through() -> None:
    """enabled=False면 토큰 없이도 통과."""
    resp = await _mw(enabled=False).dispatch(_make_request("POST", "/api/v1/posts"), _ok())
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_protected_post_without_token_rejected() -> None:
    """보호 경로 POST에 토큰이 없으면 403."""
    resp = await _mw().dispatch(_make_request("POST", "/api/v1/posts"), _ok())
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_protected_post_mismatched_token_rejected() -> None:
    """쿠키와 헤더 값이 다르면 403."""
    req = _make_request(
        "POST",
        "/api/v1/posts",
        headers={CSRF_HEADER_NAME: "header-value"},
        cookies={CSRF_COOKIE_NAME: "cookie-value"},
    )
    resp = await _mw().dispatch(req, _ok())
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_protected_post_matching_token_passes() -> None:
    """쿠키와 헤더 값이 일치하면 통과."""
    req = _make_request(
        "POST",
        "/api/v1/posts",
        headers={CSRF_HEADER_NAME: "same-token"},
        cookies={CSRF_COOKIE_NAME: "same-token"},
    )
    resp = await _mw().dispatch(req, _ok())
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_auth_path_exempt() -> None:
    """/auth/* 는 토큰 없이도 CSRF 검증 제외."""
    resp = await _mw().dispatch(_make_request("POST", "/auth/refresh"), _ok())
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_safe_get_seeds_csrf_cookie() -> None:
    """토큰 미보유 GET 응답에 csrf_token 쿠키를 시드한다."""
    resp = await _mw().dispatch(_make_request("GET", "/api/v1/posts"), _ok())
    assert resp.status_code == 200
    assert CSRF_COOKIE_NAME in resp.headers.get("set-cookie", "")


@pytest.mark.asyncio
async def test_existing_cookie_not_reseeded() -> None:
    """이미 csrf_token 쿠키를 보유하면 재시드하지 않는다."""
    req = _make_request("GET", "/api/v1/posts", cookies={CSRF_COOKIE_NAME: "existing"})
    resp = await _mw().dispatch(req, _ok())
    assert "set-cookie" not in resp.headers
