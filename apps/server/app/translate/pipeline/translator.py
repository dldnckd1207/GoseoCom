import asyncio
import json
import logging
import re

from app.config import settings

logger = logging.getLogger(__name__)


def _extract_json(text: str) -> str:
    """응답에서 JSON 객체 블록만 추출한다. thinking 텍스트가 앞뒤에 붙어도 처리."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    return match.group() if match else text


_PROMPT = """아래 고서(한문/한자) 텍스트를 한국어로 번역하세요.
반드시 다음 JSON 형식으로만 응답하세요. 두 필드 모두 반드시 한국어 문장으로 작성하세요.

- literal_text: 원문의 단어와 구조에 충실한 한국어 직역
- interpretive_text: 문맥과 뉘앙스를 살린 자연스러운 현대 한국어 의역

텍스트:
{text}

응답:
{{"literal_text": "한국어 직역", "interpretive_text": "한국어 의역"}}"""


async def run_translate(ocr_text: str) -> tuple[str, str]:
    if not settings.gemini_api_key:
        raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다.")

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=settings.gemini_api_key)
    prompt = _PROMPT.format(text=ocr_text)

    last_error: Exception = RuntimeError("번역 실패")
    for _ in range(2):
        try:
            response = await asyncio.to_thread(
                client.models.generate_content,
                model=settings.gemini_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    thinking_config=types.ThinkingConfig(thinking_budget=0),
                ),
            )
            raw = (response.text or "").strip()
            logger.info("[translator] raw response: %s", raw[:500])
            parsed: dict[str, str] = json.loads(_extract_json(raw))
            literal = parsed.get("literal_text", "")
            interpretive = parsed.get("interpretive_text", "")
            if not literal or not interpretive:
                raise ValueError("번역 결과 필드가 비어 있습니다.")
            return literal, interpretive
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(
                "[translator] parse error: %s | raw[:200]: %s",
                e,
                raw[:200] if "raw" in dir() else "N/A",
            )
            last_error = RuntimeError(f"번역 응답 파싱 실패: {str(e)[:200]}")

    raise last_error
