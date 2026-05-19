---
feature: sfr-106-translate-be
date: 2026-05-11
updated: 2026-05-14
author: cellmin
phase: design
---

# Design — SFR-106 고서 번역기 BE

## 1. 아키텍처

기존 board 모듈과 동일한 레이어 구조. BackgroundTasks를 통한 비동기 파이프라인 추가.

**파일 업로드와 번역 요청을 분리한다 (2단계). 업로드 API는 SRS §3.4 기준 신규 구현.**

```
① POST /api/v1/uploads → file_id 반환 (신규 구현 — core/files/)

② POST /api/v1/translate { file_id } → book_id 202 반환
     Router → Service → Repository (DB, 단일 commit)
                     ↓
              BackgroundTasks → pipeline/runner.py (자체 AsyncSession 생성)
                                    ↓
                              pipeline/ocr.py (Google Vision)
                                    ↓
                              pipeline/translator.py (Gemini)
```

## 2. 파일 구조

```
app/translate/
├── models.py           (기존 — 변경 없음)
├── schemas.py          (기존 — 확장)
├── repository.py       (신규)
├── service.py          (신규)
├── router.py           (신규)
└── pipeline/
    ├── __init__.py     (기존)
    ├── runner.py       (신규)
    ├── ocr.py          (신규)
    └── translator.py   (신규)
```

**변경:**
- `app/main.py` — translate_router include

## 3. DB / 시퀀스 상태

신규 마이그레이션 불필요. 기존 마이그레이션에 이미 반영되어 있음.

| 테이블 | 상태 |
|--------|------|
| `ai_tn_book` | 기존 init migration에 존재 |
| `ai_tn_book_page` | 기존 init migration에 존재 |
| `ai_th_pipeline_run` | 기존 init migration에 존재 |
| `ai_th_page_revision` | 기존 init migration에 존재 (Phase 2) |

| 시퀀스 | 상태 |
|--------|------|
| `seq_book` → `BOOK_` | `id_generator.py`에 등록, DB에 존재 |
| `seq_bpage` → `BPAGE_` | `id_generator.py`에 등록, DB에 존재 |

ID 채번: `await next_id("BOOK_", db)`, `await next_id("BPAGE_", db)`

## 4. API 명세

### POST /api/v1/uploads (신규)
- 인증: USER 이상
- Content-Type: multipart/form-data
- Body: `file: UploadFile`
- Response 201: `FileUploadResponse(file_id, original_name, url_path, file_size, file_ext)`
- 400 `FILE_SIZE_EXCEEDED`: 파일 크기 > 10MB (MVP 공용 업로드 기본 제한. 게시판 등 다른 도메인에서 정책이 달라지면 별도 조정 필요)
- 401 `UNAUTHORIZED`
- 구현 위치: `app/core/files/router.py`
- **범용 업로드** — 파일 타입 미검증. 이미지 여부는 번역 요청 시 translate service에서 검증

---

### POST /api/v1/translate
- 인증: USER 이상
- Content-Type: application/json
- Body: `{ "file_id": "FILE_00000001" }`
- 클라이언트는 먼저 `POST /api/v1/uploads`로 이미지를 업로드하고 반환된 `file_id`를 사용한다
- Response 202:
```json
{ "header": {"success": true, "code": "OK", "message": ""},
  "body": {"data": {"book_id": "BOOK_00000001", "status": "PENDING"}} }
```
- 404 `FILE_NOT_FOUND`: file_id에 해당하는 파일이 존재하지 않을 때
- 403 `FILE_ACCESS_FORBIDDEN`: 타인 소유 파일로 번역 요청
- 400 `INVALID_IMAGE_TYPE`: mime_type이 `image/`로 시작하지 않을 때
- 400 `IMAGE_SIZE_EXCEEDED`: File.file_size > 10MB
- 401 `UNAUTHORIZED`: 미인증

---

### GET /api/v1/translate/{book_id}
- 인증: USER 이상 (본인 소유)
- Response 200:
```json
{ "header": {"success": true, "code": "OK", "message": ""},
  "body": {"data": {
    "book_id": "BOOK_00000001",
    "title": "image.jpg",
    "status": "COMPLETED",
    "total_pages": 1,
    "pages": [{
      "page_no": 1,
      "ocr_text": "...",
      "literal_text": "...",
      "interpretive_text": "...",
      "ocr_engine": "GOOGLE_VISION",
      "translator_engine": "GEMINI",
      "status": "COMPLETED"
    }]
  }}}
```
- 403 `FORBIDDEN`: 타인 소유
- 404 `BOOK_NOT_FOUND`

---

### POST /api/v1/translate/list
- 인증: USER 이상
- Body: `{ "page": 1, "size": 10, "status": "COMPLETED" }` (status 선택)
- status 필터 허용값 외 입력: Pydantic Literal 타입으로 422 반환
- Repository 쿼리에 `owner_user_id = payload["sub"]` 조건 필수
- Response 200: PageData[BookListItemResponse]
```json
{ "header": {"success": true, "code": "OK", "message": ""},
  "body": {"data": {
    "items": [{"book_id": "BOOK_00000001", "title": "image.jpg", "status": "COMPLETED", "created_at": "..."}],
    "total": 1, "page": 1, "size": 10
  }}}
```

## 5. Schemas

```python
# TranslateStartRequest (신규)
file_id: str

# TranslateStartResponse
book_id: str
status: str

# BookPageResponse (from_attributes=True)
page_no: int
ocr_text: str | None
literal_text: str | None
interpretive_text: str | None
ocr_engine: str | None
translator_engine: str | None
status: str  # PENDING | COMPLETED | NO_TEXT | FAILED

# BookResponse (from_attributes=True)
book_id: str = Field(validation_alias="id")
title: str
status: str
total_pages: int
pages: list[BookPageResponse]

# BookListRequest
page: int = 1
size: int = 10
status: BookStatus | None = None  # Literal 타입으로 422 강제

# BookListItemResponse (from_attributes=True)
book_id: str = Field(validation_alias="id")
title: str
status: str
created_at: datetime
```

## 6. 파일 입력 및 Pipeline 연결

1. 클라이언트가 `POST /api/v1/uploads`로 파일을 먼저 업로드 → `file_id` 반환
2. `POST /api/v1/translate` 요청 시 `file_id`를 body로 전달
3. service에서 `FileRepository.get_by_id(file_id)`로 파일 존재 확인 + `local_path` 조회
4. 파일의 `mime_type`이 `image/`로 시작하는지 확인 (INVALID_IMAGE_TYPE)
5. Book/Page/PipelineRun 생성 → **단일 commit**
6. `pipeline_run_id`, `file_entity.local_path`를 runner에 전달

```python
# translate/service.py
async def start_translate(self, file_id: str, user_id: str, background_tasks: BackgroundTasks):
    file_entity = await self.file_repo.get_by_id(file_id)
    if not file_entity:
        raise HTTPException(404, FILE_NOT_FOUND)
    if file_entity.created_by != user_id:
        raise HTTPException(403, FILE_ACCESS_FORBIDDEN)  # 소유권 검증
    if not file_entity.mime_type.startswith("image/"):
        raise HTTPException(400, INVALID_IMAGE_TYPE)
    if file_entity.file_size > 10 * 1024 * 1024:
        raise HTTPException(400, IMAGE_SIZE_EXCEEDED)    # 크기 재검증
    # Book/Page/PipelineRun 생성
    await self.db.commit()  # 단일 commit
    background_tasks.add_task(run_pipeline, book.id, file_entity.local_path, pipeline_run.id)
```

## 7. Pipeline 흐름

```python
async def run_pipeline(book_id: str, file_local_path: str, pipeline_run_id: int) -> None:
    async with AsyncSessionLocal() as db:  # 요청 스코프 세션 아닌 독립 세션
        try:
            # PipelineRun(pipeline_run_id): PENDING → RUNNING, started_at
            # book.status = OCR_PROCESSING
            # ocr_text = await run_ocr(file_local_path)
            # book_page.ocr_text 저장
            # if not ocr_text:
            #     book.status = COMPLETED, book_page.status = NO_TEXT → return
            # book.status = TRANSLATING
            # literal, interpretive = await run_translate(ocr_text)
            # book_page.literal_text, interpretive_text, status = COMPLETED
            # book.status = COMPLETED
            # PipelineRun: COMPLETED, completed_at, duration_ms, total_cnt=1, success_cnt=1
        except Exception as e:
            # book.status = FAILED
            # PipelineRun: FAILED, fail_cnt=1, error_msg, error_stack
```

## 8. PipelineRun 생명주기

| 시점 | status | 기록 필드 |
|------|--------|-----------|
| POST 요청 처리 시 | PENDING | triggered_by, book_id, trigger_type=TRANSLATOR |
| runner 시작 시 | RUNNING | started_at |
| OCR/번역 완료 시 | COMPLETED | completed_at, duration_ms, total_cnt=1, success_cnt=1 |
| 예외 발생 시 | FAILED | fail_cnt=1, error_msg, error_stack |

## 9. Gemini 프롬프트 및 응답 규칙

Gemini는 반드시 JSON만 반환하도록 프롬프트에 명시. 응답 예시:

```json
{"literal_text": "...", "interpretive_text": "..."}
```

파싱 실패(JSON 오류, 필드 누락) 시: 1회 재시도 후 `FAILED`. `error_msg`에 원문 응답 앞 200자 저장.

## 10. 테스트 전략

- **단위 테스트**: `run_pipeline()` 직접 호출, OCR/번역 함수 mock 주입
  - 정상 흐름: COMPLETED
  - OCR 빈 텍스트: COMPLETED + page.status = NO_TEXT
  - OCR 예외: FAILED
  - Gemini 예외/파싱 실패: FAILED
- **API 테스트**: `POST /api/v1/translate` → 202 확인, `GET /{book_id}` 상태 확인
- **권한 테스트**: 타인 book_id → 403
- **업로드 API 테스트**: `POST /api/v1/uploads` → 201 + file_id 반환, 10MB 초과 → 400 FILE_SIZE_EXCEEDED
- **검증 테스트**: 존재하지 않는 file_id → 404, 타인 file_id → 403, 이미지 아닌 파일 → 400, 10MB 초과 → 400
- **E2E**: API 키 발급 후 Swagger UI로 실제 OCR + 번역 확인

## 11. 외부 의존성

- `google-cloud-vision` — 이미 설치됨
- `google-genai` — 이미 설치됨 (`google-generativeai` deprecated로 교체)

## 12. 운영 주의사항

### 업로드 메모리 이중 로드 — 코드 수정 완료

`POST /api/v1/uploads`에서 읽은 `content`를 `FileService.upload(content=content)`로 직접 전달한다.
`seek(0)` 재읽기가 제거되어 파일당 메모리 사용이 1회로 줄었다.

```python
# router.py
content = await file.read()          # 1회만 읽음
await service.upload(file, user_id, content=content)  # 재읽기 없음

# FileService.upload()
async def upload(self, file, user_id, content: bytes | None = None):
    if content is None:
        content = await file.read()  # 기존 board 업로드 경로는 그대로
```

**운영 추가 권장사항 (코드 외):**
- nginx `client_max_body_size 10m` — 진정한 조기 차단은 proxy 레벨에서만 가능. 현재 앱 코드는 전체 body를 메모리에 읽은 뒤 거부하므로 proxy limit 없이는 초과 요청도 앱 메모리까지 진입함
