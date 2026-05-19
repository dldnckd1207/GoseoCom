import asyncio

from app.config import settings


async def run_ocr(local_path: str) -> str:
    if not settings.google_vision_api_key:
        raise ValueError("GOOGLE_VISION_API_KEY가 설정되지 않았습니다.")

    from google.api_core.client_options import ClientOptions
    from google.cloud import vision

    def _call() -> str:
        client = vision.ImageAnnotatorClient(
            client_options=ClientOptions(api_key=settings.google_vision_api_key)
        )
        with open(local_path, "rb") as f:
            content = f.read()
        image = vision.Image(content=content)
        response = client.document_text_detection(image=image)
        if response.error.message:
            raise RuntimeError(f"Vision API 오류: {response.error.message}")
        return response.full_text_annotation.text or ""

    return await asyncio.to_thread(_call)
