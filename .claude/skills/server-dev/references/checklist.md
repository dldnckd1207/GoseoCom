# 개발 체크리스트

새 도메인 또는 기능을 개발할 때 확인할 사항입니다.

---

## 테스트 작성 컨벤션

### 구조

```
tests/
├── conftest.py        # db fixture, auth_client fixture, unique_email()
├── test_auth.py
├── test_db.py
└── {domain}/          # 도메인별 디렉토리로 확장 (Architecture §10 미러링)
```

### 기본 패턴

```python
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import unique_email


@pytest.mark.asyncio
async def test_{기능}_{조건}(auth_client: AsyncClient, db: AsyncSession):
    """테스트 명명: test_{검증_대상}_{조건}"""
    response = await auth_client.post("/api/v1/...", json={...})
    assert response.status_code == 201
    body = response.json()
    assert body["header"]["success"] is True
    assert body["body"]["data"]["id"].startswith("POST_")
```

**핵심 규칙:**
- `db` fixture: `NullPool` AsyncSession (이벤트 루프 충돌 방지)
- `auth_client` fixture: `app.dependency_overrides[get_db]`로 테스트 세션 주입
- `unique_email()`: 테스트마다 고유 이메일 생성 (`test-{uuid}@example.com`)
- 테스트 명명: `test_{검증_대상}_{조건}` (예: `test_require_level_no_token`)
- 실행: `uv run pytest`

---

## 환경변수 / Settings 컨벤션

`app/config.py`의 `Settings` 클래스를 통해 관리. 전체 설정은 `settings = Settings()` 싱글턴.

### 주요 환경변수

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `APP_ENV` | `development` | `development` \| `production` |
| `APP_SECRET_KEY` | `change-me` | HMAC 해시용 시크릿 (운영 시 반드시 교체) |
| `JWT_SECRET_KEY` | `change-me` | JWT 서명 시크릿 (운영 시 반드시 교체) |
| `OCR_ENGINE` | `google_vision` | `google_vision` \| `paddle_ocr` — 코드 변경 없이 전환 가능 |
| `TRANSLATOR_ENGINE` | `gemini` | `gemini` \| `anthropic` — 코드 변경 없이 전환 가능 |
| `FILE_STORAGE` | `local` | `local` \| `s3` |
| `INITIAL_ADMIN_EMAILS` | `""` | 최초 로그인 시 SYSTEM_ADMIN 자동 승급 이메일 (콤마 구분) |
| `AI_AGENT_USER_ID` | `USER_00000000` | AI 시드 계정 ID — 하드코딩 금지, `settings.ai_agent_user_id` 참조 |

### 사용법

```python
from app.config import settings
from app.core.common.enums import AppEnv, OcrEngine

if settings.app_env == AppEnv.DEVELOPMENT:
    ...  # dev 전용 로직

if settings.ocr_engine == OcrEngine.GOOGLE_VISION:
    ...  # 엔진 분기
```

---

## 파이프라인 / 비동기 작업 패턴

번역기 파이프라인 등 오래 걸리는 작업은 `BackgroundTasks`로 비동기 실행 (Architecture AD-06).

```python
from fastapi import BackgroundTasks

@router.post("/translate", response_model=ApiResponse[BookResponse], status_code=202)
async def start_translate(
    req: TranslateRequest,
    background_tasks: BackgroundTasks,
    payload: dict = require_level(UserRole.USER),
    service: TranslateService = Depends(_service),
) -> ApiResponse[BookResponse]:
    # 즉시 Book 생성 + book_id 반환
    book = await service.create_book(req, created_by=payload["sub"])
    # 파이프라인은 백그라운드 실행
    background_tasks.add_task(service.run_pipeline, book.id)
    return ApiResponse.success(book)  # header.code = SUCCESS, HTTP 202
```

**클라이언트 폴링 패턴:**
```
POST /translate          → 202, book_id 즉시 반환
GET  /books/{id}         → 200, book.status 확인
  status: PENDING → OCR_PROCESSING → TRANSLATING → COMPLETED | FAILED
```

---

## 새 도메인 추가 시

### 파일 구조

- [ ] `app/{domain}/__init__.py` 생성
- [ ] `app/{domain}/models.py` — SQLAlchemy 모델 (Base + Mixin)
- [ ] `app/{domain}/schemas.py` — Pydantic Request/Response
- [ ] `app/{domain}/repository.py` — DB 쿼리
- [ ] `app/{domain}/service.py` — 비즈니스 로직
- [ ] `app/{domain}/router.py` — FastAPI APIRouter
- [ ] `app/main.py`에 라우터 등록

### 데이터베이스

- [ ] `db/SKILL.md` 규칙에 따라 테이블명 결정 (`com_tn_`, `cms_tn_`, `ai_tn_` 등)
- [ ] Normal 테이블이면 ID-Gen: `id_generator.py`의 `_SEQ_MAP`에 PREFIX 등록
- [ ] Alembic 마이그레이션 파일 생성
- [ ] 모든 import가 `alembic/env.py`에서 인식되는지 확인

### 모델

- [ ] Normal 테이블: `TimestampMixin` 상속 (created_at, created_by, updated_at, updated_by)
- [ ] 논리 삭제 필요: `SoftDeleteMixin` 추가 상속 (del_yn, deleted_at, deleted_by)
- [ ] History 테이블: Mixin 없이 필요한 컬럼만 (created_at 정도)
- [ ] 인덱스 정의 (`__table_args__`)

### 스키마

- [ ] Response에 `model_config = {"from_attributes": True}` 포함
- [ ] `created_by`, `updated_by`는 일반 사용자 응답에서 제외
- [ ] 수정 Request: 모든 필드 Optional (None이면 현재 값 유지)

### Repository

- [ ] 조회 쿼리에 `del_yn.is_(False)` 필터 포함 (논리 삭제 테이블)
- [ ] Boolean 비교는 `== False` 대신 `.is_(False)` 사용
- [ ] `flush()`는 Repository, `commit()`은 Service에서 호출

### Service

- [ ] 존재하지 않는 리소스 → `HTTP 404` + `{DOMAIN}_NOT_FOUND`
- [ ] 소유권 위반 → `HTTP 403` + `FORBIDDEN`
- [ ] 중복 생성 → `HTTP 409` + `{DOMAIN}_ALREADY_EXISTS`
- [ ] `commit()` + `refresh()` 순서 확인 (commit 후 refresh)

### Router

- [ ] HTTP Method: GET 조회, POST 생성, PUT 수정, DELETE 삭제 (`PATCH` 사용 금지)
- [ ] 권한 레벨 적절히 설정 (`GUEST` / `USER` / `ADMIN` / `SYSTEM_ADMIN`)
- [ ] 생성 엔드포인트: `status_code=201`
- [ ] 삭제 엔드포인트: `status_code=204`, 반환 `None`
- [ ] `payload["sub"]`로 현재 사용자 ID 추출

---

## 비즈니스 규칙 체크

### 게시판/게시글/댓글 (Board 도메인)

- [ ] BBR-01: 게시글 작성은 USER 이상만
- [ ] BBR-04: 게시글 삭제 시 `comment_count` 연동 여부 검토
- [ ] BBR-05: 수정/삭제는 본인 또는 ADMIN 이상

### 번역 (Translate 도메인)

- [ ] TBR-01: 번역기는 USER 이상만
- [ ] TBR-06: 수정은 본인 소유 Book만 가능 (`book.owner_user_id == 요청자`)

### 파일 (File 도메인)

- [ ] FBR-03: 허용 MIME 타입 `image/*` 검증
- [ ] FBR-04: 최대 파일 크기 10MB 검증
- [ ] FBR-06: 파일 접근은 `GET /files/:id` 경유 (직접 경로 노출 금지)

### Phase 확인

- [ ] Phase 2~3 선반영 필드는 스키마에 포함되어 있어도 현재 로직에서 사용하지 않음
  - `secret_yn`, `like_yn`, `like_count` (Board, Phase 3)
  - `is_favorite`, `share_token`, `summary_text`, `keywords` (Translate, Phase 2)
  - `is_filtered`, `filter_reason` (Comment, Phase 3)
