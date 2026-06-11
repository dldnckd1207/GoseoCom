import asyncio
import json
import re

from app.config import settings

_PROMPT = """아래는 고서(한문/한자) 텍스트의 OCR 원문과 번역문입니다.
반드시 다음 JSON 형식으로만 응답하세요.

- summary: 번역문을 바탕으로 한 2~5줄 핵심 요약 (한국어)
- keywords: OCR 원문에서 추출한 주요 한자어 목록. 각 항목은 word(한자), reading(한국어 독음), meaning(한국어 뜻) 포함. 최대 20개.

OCR 원문:
{ocr_text}

번역문:
{interpretive_text}

응답:
{{"summary": "핵심 요약", "keywords": [{{"word": "한자", "reading": "독음", "meaning": "뜻"}}]}}"""


async def run_analyze(ocr_text: str, interpretive_text: str) -> tuple[str, list[dict[str, object]]]:
    if not settings.gemini_api_key:
        raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다.")

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=settings.gemini_api_key)
    prompt = _PROMPT.format(ocr_text=ocr_text, interpretive_text=interpretive_text)

    response = await asyncio.wait_for(
        client.aio.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                thinking_config=types.ThinkingConfig(thinking_budget=0),
            ),
        ),
        timeout=30.0,
    )

    raw = (response.text or "").strip()
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    parsed: dict[str, object] = json.loads(match.group() if match else raw)
    summary: str = str(parsed.get("summary", ""))
    raw_keywords = parsed.get("keywords", [])
    keywords: list[dict[str, object]] = raw_keywords if isinstance(raw_keywords, list) else []

    for kw in keywords:
        word = str(kw.get("word", ""))
        kw["count"] = len(re.findall(re.escape(word), ocr_text)) if word else 0

    return summary, keywords
