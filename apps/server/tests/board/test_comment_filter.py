"""#120: 악성 댓글 AI 필터링 — comment_filter.py 단위 테스트"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.board.comment_filter import run_filter


@pytest.mark.asyncio
async def test_run_filter_malicious() -> None:
    """악성 댓글 판별 — is_malicious=True 반환"""
    mock_response = MagicMock()
    mock_response.text = '{"is_malicious": true, "reason": "욕설 포함", "confidence": 0.95}'

    with (
        patch("app.board.comment_filter.settings") as mock_settings,
        patch("app.board.comment_filter.genai", create=True) as mock_genai,
    ):
        mock_settings.gemini_api_key = "test-key"
        mock_settings.gemini_model = "gemini-2.5-flash"
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client
        mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)

        # asyncio.wait_for patch
        with patch(
            "app.board.comment_filter.asyncio.wait_for", new=AsyncMock(return_value=mock_response)
        ):
            is_malicious, reason, confidence = await run_filter("이 욕설 댓글")

    assert is_malicious is True
    assert "욕설" in reason
    assert confidence == pytest.approx(0.95)


@pytest.mark.asyncio
async def test_run_filter_clean() -> None:
    """정상 댓글 판별 — is_malicious=False 반환"""
    mock_response = MagicMock()
    mock_response.text = '{"is_malicious": false, "reason": "", "confidence": 0.02}'

    with (
        patch("app.board.comment_filter.settings") as mock_settings,
        patch(
            "app.board.comment_filter.asyncio.wait_for", new=AsyncMock(return_value=mock_response)
        ),
        patch("app.board.comment_filter.genai", create=True) as mock_genai,
    ):
        mock_settings.gemini_api_key = "test-key"
        mock_settings.gemini_model = "gemini-2.5-flash"
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client

        is_malicious, reason, _ = await run_filter("안녕하세요 좋은 댓글입니다")

    assert is_malicious is False
    assert reason == ""


@pytest.mark.asyncio
async def test_run_filter_no_api_key() -> None:
    """GEMINI_API_KEY 미설정 시 ValueError"""
    with patch("app.board.comment_filter.settings") as mock_settings:
        mock_settings.gemini_api_key = ""

        with pytest.raises(ValueError, match="GEMINI_API_KEY"):
            await run_filter("댓글")


@pytest.mark.asyncio
async def test_run_filter_json_parse_error() -> None:
    """JSON 파싱 실패 시 RuntimeError"""
    mock_response = MagicMock()
    mock_response.text = "invalid json response"

    with (
        patch("app.board.comment_filter.settings") as mock_settings,
        patch(
            "app.board.comment_filter.asyncio.wait_for", new=AsyncMock(return_value=mock_response)
        ),
        patch("app.board.comment_filter.genai", create=True) as mock_genai,
        pytest.raises(RuntimeError, match="JSON 파싱 실패"),
    ):
        mock_settings.gemini_api_key = "test-key"
        mock_settings.gemini_model = "gemini-2.5-flash"
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client

        await run_filter("댓글")
