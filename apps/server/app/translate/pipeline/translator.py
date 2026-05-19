import asyncio
import json

from app.config import settings

_PROMPT = """아래 고서 텍스트를 번역하세요.
반드시 다음 JSON 형식으로만 응답하세요.

텍스트:
{text}

응답:
{{"literal_text": "직역 내용", "interpretive_text": "의역 내용"}}"""


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
                config=types.GenerateContentConfig(response_mime_type="application/json"),
            )
            parsed: dict[str, str] = json.loads((response.text or "").strip())
            literal = parsed.get("literal_text", "")
            interpretive = parsed.get("interpretive_text", "")
            if not literal or not interpretive:
                raise ValueError("번역 결과 필드가 비어 있습니다.")
            return literal, interpretive
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            last_error = RuntimeError(f"번역 응답 파싱 실패: {str(e)[:200]}")

    raise last_error
