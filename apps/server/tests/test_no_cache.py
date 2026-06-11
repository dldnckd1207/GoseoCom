"""API/Auth 응답 Cache-Control: no-store 미들웨어 테스트"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_auth_response_has_no_store(auth_client: AsyncClient) -> None:
    """OAuth 시작 리다이렉트가 캐싱되면 만료된 state 재사용으로 INVALID_STATE 발생."""
    response = await auth_client.get("/auth/google")
    assert response.headers.get("Cache-Control") == "no-store"


@pytest.mark.asyncio
async def test_api_response_has_no_store(auth_client: AsyncClient) -> None:
    response = await auth_client.get("/api/v1/users/me")
    assert response.headers.get("Cache-Control") == "no-store"


@pytest.mark.asyncio
async def test_non_api_path_not_affected(auth_client: AsyncClient) -> None:
    """/files/ 등 정적 리소스 경로는 캐싱 이점 유지를 위해 헤더를 강제하지 않는다."""
    response = await auth_client.get("/health")
    assert "Cache-Control" not in response.headers
