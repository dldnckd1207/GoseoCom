"""악성 댓글 AI 판별 — Gemini 기반"""

import asyncio
import json
import re

from app.config import settings

_PROMPT = """당신은 한국어 게시판 댓글 모더레이터입니다.
아래 댓글이 악성인지 판단하고 반드시 다음 JSON 형식으로만 응답하세요.

판단 기준:
- 욕설: 비속어, 욕설, 모욕적 표현 포함
- 혐오 표현: 특정 집단(성별·인종·종교·장애 등)에 대한 혐오·차별
- 스팸: 광고·홍보, 의미 없는 반복 문자

댓글:
{content}

응답:
{{"is_malicious": true/false, "reason": "악성 사유 (정상이면 빈 문자열)", "confidence": 0.0}}"""


async def run_filter(content: str) -> tuple[bool, str, float]:
    """Gemini로 댓글 악성 여부를 판별한다.

    Returns: (is_malicious, reason, confidence)
    Raises:
        ValueError: GEMINI_API_KEY 미설정
        RuntimeError: API 오류 또는 JSON 파싱 실패
    """
    if not settings.gemini_api_key:
        raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다.")

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=settings.gemini_api_key)
    prompt = _PROMPT.format(content=content)

    response = await asyncio.wait_for(
        client.aio.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                thinking_config=types.ThinkingConfig(thinking_budget=0),
            ),
        ),
        timeout=10.0,
    )

    raw = (response.text or "").strip()
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    try:
        parsed: dict[str, object] = json.loads(match.group() if match else raw)
    except (json.JSONDecodeError, AttributeError) as e:
        raise RuntimeError(f"Gemini 응답 JSON 파싱 실패: {raw[:200]}") from e

    is_malicious = bool(parsed.get("is_malicious", False))
    reason = str(parsed.get("reason", ""))
    raw_conf = parsed.get("confidence", 0.0)
    confidence = float(raw_conf) if isinstance(raw_conf, int | float) else 0.0
    return is_malicious, reason, confidence
