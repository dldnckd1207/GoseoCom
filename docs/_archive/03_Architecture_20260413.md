# Architecture (시스템 아키텍처)

---

| 항목 | 내용 |
|------|------|
| **제품명** | Haedok AI (解讀 AI) |
| **버전** | v1.0 |
| **작성일** | 2026-04-09 |
| **작성자** | - |
| **관련 문서** | [PRD](01_PRD.md), [SRS](02_SRS.md) |

---

## 1. 개요

### 1.1 목적

본 문서는 Haedok AI 시스템의 아키텍처를 정의한다. 모노레포 구조, 컴포넌트 책임과 경계, 컴포넌트 간 통신, 데이터 흐름, 배포 토폴로지, 핵심 설계 결정을 포함한다. SRS §2(시스템 구성 개요)에서 다룬 high-level 구성을 구체화하는 문서이며, 도메인 모델과 DB 스키마는 별도 문서로 관리한다.

### 1.2 범위

- 시스템의 정적 구조 (컴포넌트, 모듈, 디렉토리)
- 시스템의 동적 구조 (요청 흐름, 파이프라인 실행)
- 외부 의존성과의 경계
- Phase별 아키텍처 변화

다음은 본 문서의 범위 외이다:
- 도메인 개념 정의 → [Domain](04_Domain.md)
- DB 스키마 → [ERD](05_ERD.md)
- 기능 요구사항 → [SRS](02_SRS.md)

### 1.3 관련 문서

- [PRD](01_PRD.md) — 제품 요구사항
- [SRS](02_SRS.md) — 소프트웨어 요구사항
- [Domain](04_Domain.md) — 도메인 모델
- [ERD](05_ERD.md) — DB 스키마

---

## 2. 아키텍처 원칙

| 원칙 | 설명 |
|------|------|
| **Phase별 단계적 확장** | Phase 1~3 로드맵에 따라 컴포넌트를 점진적으로 추가한다. 초기에는 단순함을 우선한다. |
| **OCR/AI 엔진 추상화** | OCR과 번역 엔진은 인터페이스로 추상화하여 1순위/2순위 구현체 교체가 가능하다. |
| **Stateless API** | 백엔드 API는 상태 없이 동작하며, 영속 상태는 PostgreSQL에 저장한다. |
| **모노레포** | `apps/client`, `apps/server`, `apps/admin`이 하나의 저장소를 공유하되 독립적으로 빌드/배포 가능하다. |
| **파이프라인 비동기 실행** | OCR + 번역 파이프라인은 백그라운드로 실행되며, 결과는 댓글 등록 형태로 사용자에게 전달된다. |
| **단일 백엔드 서비스** | API, 파이프라인, 스케줄러를 단일 FastAPI 서비스로 통합 운영하여 초기 운영 복잡도를 낮춘다. |

---

## 3. 시스템 구성

### 3.1 전체 구성도

```
┌─────────────────────────────────────────────────────────────────┐
│                          Browser (PC)                            │
└──────────────┬───────────────────────────────┬──────────────────┘
               │                               │
               │ HTTP/REST                     │ HTTP/REST
               │                               │ (Phase 3)
┌──────────────▼─────────────┐  ┌──────────────▼──────────────────┐
│      apps/client            │  │       apps/admin                │
│      (React / Remix)        │  │       (React / Remix)           │
│   - 게시판 / 번역기           │  │   - 관리자 페이지                 │
└──────────────┬─────────────┘  └──────────────┬──────────────────┘
               │                               │
               └───────────────┬───────────────┘
                               │
                               │ REST API (JSON)
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│                       apps/server                                │
│                   (FastAPI / Python 3.12+)                       │
│                                                                  │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌───────────┐ │
│  │ API Layer  │→ │  Service   │→ │ Repository │→ │  Domain   │ │
│  │  (Routers) │  │   Layer    │  │   Layer    │  │  Models   │ │
│  └────────────┘  └─────┬──────┘  └─────┬──────┘  └───────────┘ │
│                        │               │                        │
│                        ▼               │                        │
│              ┌──────────────────┐      │                        │
│              │   AI Pipeline    │      │                        │
│              │  (OCR + Trans)   │      │                        │
│              └────┬─────────────┘      │                        │
│                   │                    │                        │
│  ┌────────────┐   │                    │                        │
│  │ Scheduler  │───┘                    │                        │
│  │ (1m tick)  │                        │                        │
│  └────────────┘                        │                        │
└────────────────────────────────────────┼────────────────────────┘
                       │                 │
                       │ External API    │ SQL
                       │                 │
        ┌──────────────▼─────┐  ┌────────▼──────────┐
        │  PaddleOCR /       │  │   PostgreSQL 16   │
        │  Google Vision     │  │                   │
        │  Gemini / Claude   │  │   (Docker)        │
        └────────────────────┘  └───────────────────┘

        ┌────────────────────┐
        │   File Storage     │
        │   (Local Volume)   │  ← 업로드 이미지
        └────────────────────┘
```

### 3.2 컴포넌트 책임

| 컴포넌트 | 책임 | Phase |
|---------|------|-------|
| `apps/client` | 다중 게시판(LIST/IMAGE/QNA) UI, 번역기 UI(Phase 2), REST API 호출, 결과 렌더링 | 1~ |
| `apps/admin` | 관리자 UI (파이프라인 ON/OFF, 자동답변 시간 설정, 댓글 관리, 게시글 관리) | 3 |
| `apps/server` API Layer | HTTP 요청 처리, 입력 검증(Pydantic), 응답 직렬화 | 1~ |
| `apps/server` Service Layer | 비즈니스 로직, 트랜잭션 경계, 파이프라인 트리거 | 1~ |
| `apps/server` Repository Layer | DB 접근 추상화 (SQLAlchemy) | 1~ |
| AI Pipeline | OCR → 번역 → 후처리. 외부 엔진 호출 및 결과 정규화. 진입점=번역기, 재사용=게시판 자동 답변(설정 ON 시) | 2~ |
| Scheduler | 주기적 작업. Phase 1: 텍스트 기반 자동 답변. Phase 2+: 파이프라인 연동 자동 답변. Phase 3: 악성댓글 검수 | 1~ |
| PostgreSQL | 게시글/댓글/이미지 메타/OCR/번역 영속 저장 | 1~ |
| File Storage | 업로드 이미지 바이너리 저장 | 1~ |

### 3.3 외부 의존성

| 의존성 | 용도 | 추상화 위치 |
|--------|------|-------------|
| PaddleOCR | OCR 텍스트 추출 (1순위) | `pipeline/ocr/PaddleOcrEngine` |
| Google Vision API | OCR 텍스트 추출 (2순위) | `pipeline/ocr/GoogleVisionEngine` |
| Gemini Flash API | AI 번역/자동답변 (1순위) | `pipeline/translator/GeminiTranslator` |
| Claude Haiku API | AI 번역/자동답변 (2순위) | `pipeline/translator/ClaudeTranslator` |

---

## 4. 데이터 흐름

> **참고**: Phase 1은 파이프라인이 존재하지 않는다. 자동 답변은 게시글 텍스트만 사용한다. 파이프라인은 Phase 2에서 번역기(SFR-200)를 통해 도입되며, 게시판 자동 답변은 설정에 따라 파이프라인을 재사용한다(SFR-205).

### 4.1 게시글 작성 (SFR-101, Phase 1)

파일 업로드와 글 작성이 분리된다. 파일은 먼저 업로드되어 `file` 레코드가 생성되고, 글 작성 시 `file_id` 리스트를 전달하여 `file_map`으로 다형 매핑된다.

```
[Client]                [API Layer]        [Service]          [Storage]      [DB]
   |                        |                  |                  |            |
   |-- (1) 파일 선업로드     |                  |                  |            |
   |-- POST /files -------->|                  |                  |            |
   |  (multipart, file)     |                  |                  |            |
   |                        |-- upload_file ──>|                  |            |
   |                        |                  |-- validate type/size         |
   |                        |                  |-- store binary ->|            |
   |                        |                  |-- insert file ─────────────->|
   |                        |<-- file_id ──────|                  |            |
   |<-- 201 { file_id } ----|                  |                  |            |
   |                                                                           |
   |-- (2) 글 작성          |                  |                  |            |
   |-- POST /boards/:code/posts -->|           |                  |            |
   |  (title, content,      |                  |                  |            |
   |   file_ids[])          |                  |                  |            |
   |                        |-- create_post ─->|                  |            |
   |                        |                  |-- find board by code ───────>|
   |                        |                  |-- validate board.attach_* (count/ext) |
   |                        |                  |-- save post (board_id) ────->|
   |                        |                  |-- for each file_id:          |
   |                        |                  |   insert file_map ──────────>|
   |                        |                  |   (target_type=POST, target_id=post.id) |
   |                        |<-- post_id ──────|                  |            |
   |<-- 201 Created --------|                  |                  |            |
```

**특징**:
- 파일 업로드와 글 작성이 분리되어, 업로드 진행 중에도 글 본문 편집 가능하고 미리보기 즉시 렌더링 가능
- `file_map`은 다형 매핑 (`target_type` ∈ {`POST`, `COMMENT`, ...}) — 다른 엔티티도 동일 파일 테이블 재사용
- Phase 1에서 게시글 작성 자체는 OCR/파이프라인을 트리거하지 않음
- 첨부 개수/확장자 검증은 해당 게시판 설정(`boards.attach_*`)에 따름

> `file`, `file_map` 스키마 상세는 ERD/Domain 문서에서 확정.

### 4.2 AI 자동 답변 — Phase 1 (SFR-104, 텍스트 기반)

```
[Scheduler]              [Service]              [AI API]             [DB]
   |                        |                       |                  |
   |-- tick (1m) ─────────->|                       |                  |
   |                        |-- find target posts ────────────────────>|
   |                        |   WHERE board.auto_reply_enabled=true    |
   |                        |     AND comment_count = 0                |
   |                        |     AND age > board.auto_reply_delay_min |
   |                        |     AND auto_reply_status=pending        |
   |                        |<-- post[] ──────────────────────────────|
   |                        |-- for each post ────->|                  |
   |                        |   (title + content)   |-- Gemini call ─>|
   |                        |                       |<-- reply text ──|
   |                        |-- save comment (author_type=ai_auto) ──>|
   |                        |-- update auto_reply_status=completed ──>|
```

**특징**:
- 이미지 첨부 여부와 무관하게 **텍스트만** AI에 전달
- 게시판별 `auto_reply_delay_min` 설정 사용 (기본 5분)

### 4.3 AI 자동 답변 — Phase 2 확장 (SFR-205, 파이프라인 연동)

```
[Scheduler]              [Service]                 [Pipeline]              [DB]
   |                        |                          |                     |
   |-- tick (1m) ─────────->|                          |                     |
   |                        |-- find target posts ────────────────────────-->|
   |                        |   WHERE board.auto_reply_enabled=true          |
   |                        |     AND board.pipeline_enabled=true            |
   |                        |     AND comment_count = 0                      |
   |                        |     AND age > board.auto_reply_delay_min       |
   |                        |     AND auto_reply_status=pending              |
   |                        |<-- post[] ──────────────────────────────────--|
   |                        |-- for each post ───────->|                     |
   |                        |   (images)               |-- OCR (PaddleOCR)   |
   |                        |                          |-- Translate (Gemini)|
   |                        |                          |-- Post-process     |
   |                        |                          |   (요약/키워드/추천) |
   |                        |<-- pipeline result ──────|                     |
   |                        |-- save comment (author_type=ai_pipeline) ─────>|
   |                        |-- update auto_reply_status=completed ─────────>|
```

**특징**:
- `pipeline_enabled=false`인 게시판은 §4.2 경로 유지
- `pipeline_enabled=true`인 게시판만 본 경로 실행
- 파이프라인 모듈은 §4.4 번역기와 동일 구현을 재사용

### 4.4 고서 번역기 (SFR-200, Phase 2 — 파이프라인 정식 진입점)

```
[Client]                [API Layer]        [Service]         [Pipeline]        [DB]
   |                        |                  |                  |              |
   |-- POST /translate ────>|                  |                  |              |
   |  (image OR text)       |                  |                  |              |
   |                        |-- run_pipeline ─>|                  |              |
   |                        |                  |-- OCR (image) ──>|              |
   |                        |                  |-- Translate ────>|              |
   |                        |                  |<-- result ──────|              |
   |                        |                  |-- save result ────────────────>|
   |                        |<-- result ───────|                  |              |
   |<-- 200 OK -------------|                  |                  |              |
   |   (직역, 의역, 요약)      |                  |                  |              |
```

### 4.5 번역 결과 수정 (SFR-201, Phase 2)

```
[Client]                [API Layer]        [Service]         [DB]
   |                        |                  |               |
   |-- PATCH /translations/:id ──>|            |               |
   |  (literal? interpretive?)   |             |               |
   |                        |-- update_translation ─>|          |
   |                        |                  |-- load current ──>|
   |                        |                  |-- save revision ─>| (translation_revisions)
   |                        |                  |-- update translation ─>|
   |                        |<-- updated ──────|               |
   |<-- 200 OK -------------|                  |               |
```

수정 이력은 별도 테이블(`translation_revisions`)로 append-only 저장하여 원본 복구가 가능하다.

### 4.6 악성댓글 필터링 (SFR-301, Phase 3)

```
[Scheduler]              [Service]              [Pipeline]           [DB]
   |                        |                       |                  |
   |-- tick (configurable) >|                       |                  |
   |                        |-- find unchecked comments ─────────────>|
   |                        |<-- comment[] ──────────────────────────|
   |                        |-- for each comment ──>|                  |
   |                        |                       |-- AI judge (Gemini)
   |                        |                       |<-- malicious? ──|
   |                        |-- update is_filtered ────────────────────>|
```

---

## 5. 백엔드 아키텍처 (apps/server)

### 5.1 레이어 구조

```
┌─────────────────────────────────────────┐
│  API Layer (FastAPI Routers)            │  ← HTTP, 입력 검증, 직렬화
├─────────────────────────────────────────┤
│  Service Layer                          │  ← 비즈니스 로직, 트랜잭션
├─────────────────────────────────────────┤
│  Repository Layer                       │  ← DB 접근 추상화
├─────────────────────────────────────────┤
│  Domain / ORM Models                    │  ← SQLAlchemy 엔티티
└─────────────────────────────────────────┘
```

의존성 방향:
```
API → Service → Repository → ORM → DB
         │
         ├──→ Pipeline → External APIs
         │
         └──→ (Scheduler가 Service를 호출)
```

### 5.2 모듈 구성

| 모듈 | 책임 |
|------|------|
| `app/api` | FastAPI 라우터, 요청/응답 스키마(Pydantic), 의존성 주입 |
| `app/services` | 게시판/댓글/파이프라인/스케줄링 비즈니스 로직 |
| `app/repositories` | SQLAlchemy 기반 CRUD 추상화 |
| `app/domain` | ORM 엔티티, 도메인 Enum |
| `app/pipeline` | OCR/번역 엔진 인터페이스 및 구현체, 파이프라인 오케스트레이션 |
| `app/scheduler` | 주기적 작업 (APScheduler 등) |
| `app/storage` | 파일 저장소 추상화 (로컬/S3 호환) |
| `app/core` | 설정(Settings), DB 연결, 공통 예외, 로깅 |
| `app/main.py` | FastAPI 앱 부트스트랩 |

### 5.3 데이터 변환 경계

```
HTTP Request (JSON)
   ↓ Pydantic (RequestSchema)
Service Input (DTO/Pydantic)
   ↓ Service
ORM Entity (SQLAlchemy)
   ↓ Repository
PostgreSQL
   ↑ Repository
ORM Entity
   ↑ Service
Service Output (DTO/Pydantic)
   ↑ Pydantic (ResponseSchema)
HTTP Response (JSON)
```

---

## 6. AI 파이프라인 아키텍처

> **파이프라인은 Phase 2에서 도입된다.** Phase 1에서는 존재하지 않는다.
>
> **정식 진입점**: 고서 번역기(SFR-200). 사용자가 이미지/텍스트를 직접 입력하는 `/translate` 페이지가 파이프라인을 사용하는 1차 경로.
>
> **재사용처**: 게시판 자동 답변(SFR-205). 게시판 설정 `pipeline_enabled=true`일 때만 동일 파이프라인 모듈을 재호출.

### 6.1 인터페이스 추상화

OCR과 번역 엔진은 Protocol/추상 클래스로 정의되어 구현체 교체가 가능하다.

```python
# 개념 예시 (실제 시그니처는 구현 단계에서 확정)

class OcrEngine(Protocol):
    name: str
    def extract(self, image_bytes: bytes) -> OcrResultDTO: ...

class Translator(Protocol):
    name: str
    def translate(self, text: str) -> TranslationDTO: ...
```

### 6.2 구현체 매핑

| 인터페이스 | 1순위 구현 | 2순위 구현 | 전환 조건 |
|-----------|-----------|-----------|-----------|
| `OcrEngine` | `PaddleOcrEngine` | `GoogleVisionEngine` | 인식률이 목표(70%) 미달 |
| `Translator` | `GeminiTranslator` | `ClaudeTranslator` | 사용자 수정 비율 50% 초과 또는 무료 한도 초과 |

엔진 선택은 환경 변수/Settings로 주입한다. 런타임 동적 전환은 Phase 1 범위 외이다.

### 6.3 파이프라인 실행 흐름

```
[Trigger]
  ├─ 번역기 페이지 (사용자 요청, 정식 진입점)
  └─ 게시판 자동 답변 (스케줄러, board.pipeline_enabled=true일 때만)
       │
       ▼
[PipelineRun.create] (status=pending)
       │
       ▼
[OCR Step]                ── PaddleOCR / Google Vision
   ↓ OcrResult 저장
       │
       ▼
[Translation Step]        ── Gemini / Claude
   ↓ Translation 저장 (직역/의역)
       │
       ▼
[Post-process Step]       ── (Phase 2) 요약, 키워드, 빈도수, 참고자료 추천
       │
       ▼
[Persist Result]
   ├─ 번역기 트리거: 클라이언트로 응답 반환 (선택적으로 번역 결과 저장)
   └─ 게시판 자동 답변 트리거: Comment 등록 (author_type=ai_pipeline)
       │
       ▼
[PipelineRun.update] (status=completed | failed)
```

### 6.4 실행 방식

| Phase | 방식 | 비고 |
|-------|------|------|
| Phase 1 | FastAPI `BackgroundTasks` | 단순함 우선, 단일 인스턴스 가정 |
| Phase 2 | 동일 (필요 시 작업 큐 검토) | 부하/장애 격리 필요 시 Celery/RQ 도입 |
| Phase 3 | 작업 큐 권장 | 관리자 페이지에서 재실행/재시도 필요 |

---

## 7. 프론트엔드 아키텍처 (apps/client)

### 7.1 라우팅 (Remix)

| 경로 | 화면 | Phase |
|------|------|-------|
| `/` | 홈 (게시판 목록 또는 기본 게시판으로 리다이렉트) | 1 |
| `/boards` | 게시판 목록 | 1 |
| `/boards/:code` | 게시판 상세 (게시글 목록, `board_type`에 따라 LIST/IMAGE/QNA 렌더링) | 1 |
| `/boards/:code/posts/new` | 게시글 작성 | 1 |
| `/boards/:code/posts/:id` | 게시글 상세 (댓글 포함) | 1 |
| `/boards/:code/posts/:id/edit` | 게시글 수정 | 1 |
| `/translate` | 번역기 페이지 | 2 |
| `/translate/:id` | 번역 결과 공유 페이지 | 2 |

### 7.2 데이터 로딩

- Remix `loader`로 서버 데이터 페칭
- 변형은 `action` 사용 (게시글 작성/수정/삭제)
- 클라이언트 상태는 React state 위주, 전역 상태 라이브러리는 미도입

### 7.3 파이프라인 결과 표시

- 게시글 상세 페이지에서 댓글 목록을 polling 또는 SSE로 갱신 (Phase 1: polling)
- AI 댓글 구분 표시
  - `author_type=ai_auto` — 텍스트 기반 자동 답변 (Phase 1~)
  - `author_type=ai_pipeline` — 파이프라인 기반 자동 답변 (Phase 2~, `pipeline_enabled` 게시판)
- 직역/의역은 나란히 비교 가능한 레이아웃

### 7.4 게시판별 렌더링

- `LIST` — 테이블/리스트 뷰 (일반 게시판)
- `IMAGE` — 카드/갤러리 뷰 (이미지 중심 게시판)
- `QNA` — 아코디언 뷰 (질답형 게시판)
- `board_type` 값을 기준으로 동일 데이터에 대해 다른 컴포넌트로 렌더링

---

## 8. 데이터 저장소

### 8.1 PostgreSQL

| 항목 | 설정 |
|------|------|
| 버전 | 16+ |
| 운영 | 단일 인스턴스, Docker Compose |
| ORM | SQLAlchemy 2.x |
| 마이그레이션 | Alembic |
| 연결 풀 | SQLAlchemy 기본 풀 |

상세 스키마는 [ERD](05_ERD.md)에서 정의한다.

### 8.2 파일 스토리지

| Phase | 저장소 | 비고 |
|-------|--------|------|
| Phase 1 | 로컬 볼륨 (`./data/uploads`) | Docker Compose volume mount |
| Phase 2 이후 | S3 호환 스토리지 검토 | 운영 환경 분리 시 |

파일 경로는 DB(`file.storage_path`)에만 저장하고, 백엔드는 `Storage` 추상화를 통해 접근한다. 엔티티(게시글/댓글 등)와의 연결은 `file_map`(다형 매핑 테이블)으로 관리한다.

---

## 9. 비기능 요구사항 매핑 (NFR)

SRS §8의 비기능 요구사항을 아키텍처상에서 어떻게 달성하는지 매핑한다.

### 9.1 성능

| NFR | 목표 | 달성 전략 |
|-----|------|----------|
| OCR + 번역 파이프라인 | 30초 이내 (A4 1페이지) | BackgroundTasks 비동기 실행, 엔진별 타임아웃 설정, 이미지 리사이즈 전처리 |
| 게시판 API 응답 | 500ms 이내 | Repository 단일 쿼리 기준, N+1 회피, 목록은 페이지네이션 + 인덱스 |
| 이미지 업로드 | 최대 10MB | API Layer에서 Content-Length/파일 크기 사전 검증 |

### 9.2 보안

| NFR | 대응 위치 | 구현 방식 |
|-----|----------|----------|
| 파일 업로드 검증 | `app/api` (업로드 라우터) | MIME 타입 화이트리스트(image/*), 크기 제한 10MB, 확장자 검증 |
| XSS | `apps/client`, `apps/admin` | React의 기본 이스케이핑 + `dangerouslySetInnerHTML` 금지 정책, CSP 헤더 |
| SQL Injection | `app/repositories` | SQLAlchemy ORM + 파라미터 바인딩 (raw SQL 금지) |
| CORS | `app/main.py` | FastAPI CORS 미들웨어, 허용 오리진 Settings 주입 |
| 입력 검증 | `app/api` | Pydantic RequestSchema 필수 |

### 9.3 가용성 / 배포

- Docker Compose 기반 단일 호스트 운영 (§11 참조)
- 각 앱(client/server/admin)은 독립 이미지로 빌드 가능 → 부분 배포 가능
- 데이터(`postgres`, `uploads/`)는 Docker volume으로 영속화

### 9.4 호환성

- Remix는 최신 Chrome/Edge/Firefox 대상 브라우저 번들 생성
- PC 우선, 모바일은 반응형 레이아웃으로 대응

---

## 10. 디렉토리 구조

```
haedok-ai/
├── apps/
│   ├── client/              # React / Remix
│   │   ├── app/
│   │   ├── public/
│   │   ├── package.json
│   │   └── ...
│   ├── server/              # FastAPI
│   │   ├── app/
│   │   │   ├── api/
│   │   │   ├── services/
│   │   │   ├── repositories/
│   │   │   ├── domain/
│   │   │   ├── pipeline/
│   │   │   │   ├── ocr/
│   │   │   │   └── translator/
│   │   │   ├── scheduler/
│   │   │   ├── storage/
│   │   │   ├── core/
│   │   │   └── main.py
│   │   ├── alembic/
│   │   ├── tests/
│   │   ├── pyproject.toml
│   │   └── ...
│   └── admin/               # Phase 3
├── docs/
│   ├── specs/               # PRD, SRS, Architecture, Domain, ERD
│   ├── meetings/
│   ├── reports/
│   └── _samples/
├── docker-compose.yml
├── README.md
└── LICENSE
```

> 위 구조는 권장안이며, 구현 단계에서 일부 조정 가능하다.

---

## 11. 배포 토폴로지

### 11.1 로컬 개발

```
[Developer Machine]
  ├─ apps/client     (npm run dev, port 3000)
  ├─ apps/server     (uv run uvicorn, port 8000)
  └─ Docker Compose
       ├─ postgres:16        (port 5432)
       └─ (선택) paddleocr   (별도 컨테이너 검토)
```

### 11.2 Docker Compose 통합 실행

```
[Host]
  └─ Docker Compose
       ├─ client    (Remix build)
       ├─ server    (FastAPI + Pipeline + Scheduler)
       ├─ postgres
       └─ volumes
            └─ uploads/    (이미지 저장)
```

### 11.3 클라우드 배포

| Phase | 방식 | 비고 |
|-------|------|------|
| Phase 1 | 단일 호스트 Docker Compose | 개발/데모 용도, 로컬 볼륨 사용 |
| Phase 2 | 단일 호스트 Docker Compose 유지 | 파일 스토리지 S3 호환 이전 검토 (§8.2) |
| Phase 3 | 운영 토폴로지 확정 | server 인스턴스 분리, PostgreSQL 매니지드 DB 이전, `apps/admin` 별도 배포 단위 검토 |

정확한 운영 토폴로지(호스트 스펙, 리전, 보안 그룹)는 Phase 3 배포 착수 시점에 별도 배포 계획서로 확정한다.

---

## 12. 핵심 설계 결정 (ADR Lite)

| ID | 결정 | 이유 | 트레이드오프 |
|----|------|------|--------------|
| **AD-01** | 모노레포 채택 | 3명이 병렬 개발하면서 문서/타입/마이그레이션을 한 저장소에서 추적 | 빌드/CI 복잡도 증가 |
| **AD-02** | OCR/번역 엔진 추상화 | 1순위 무료 엔진으로 시작, 품질 부족 시 2순위로 전환 | 인터페이스 설계 비용 |
| **AD-03** | 단일 FastAPI 백엔드 | API + 파이프라인 + 스케줄러를 한 서비스에 통합 (초기 단순함) | 향후 분리 시 리팩토링 비용 |
| **AD-04** | PostgreSQL 단일 DB | 관계형 데이터 + 향후 검색(pg_trgm, FTS) 확장 가능 | 검색 특화 시 별도 엔진(예: Elasticsearch) 필요 가능 |
| **AD-05** | Phase 1 비인증 | 초기 개발 속도 우선, 인증은 Phase 3 | 악의적 사용 방어 제한적 |
| **AD-06** | 파이프라인 BackgroundTasks (Phase 1) | 별도 큐 인프라 없이 비동기 실행 | 단일 인스턴스 가정, 장애 격리 약함 |
| **AD-07** | author_type 필드로 댓글 출처 구분 | user/ai_auto/ai_pipeline을 단일 테이블에서 관리 | 출처별 통계/필터링은 application 레벨 |
| **AD-08** | PaddleOCR은 `apps/server` 프로세스 내 임베드 (Phase 1), 필요 시 별도 컨테이너 분리 (Phase 2+) | 초기 단일 배포 유닛으로 단순화, 모델 로드 비용은 프로세스 기동 1회로 흡수 | 서버 메모리 점유 증가, OCR 장애가 API에 전파될 수 있음 |

---

## 13. Phase별 아키텍처 변화

### Phase 1

**구성**: `apps/client` + `apps/server` + PostgreSQL

**핵심 컴포넌트**:
- 다중 게시판 스키마 및 API (SFR-105) — `boards` 테이블, `board_type`(LIST/IMAGE/QNA)
- 게시판별 CRUD API (SFR-101) — 게시글/댓글, 이미지 첨부(로컬 저장)
- AI 자동 답변 스케줄러 (SFR-104) — **텍스트 기반**, 파이프라인 없음
- 게시판별 설정 기반 자동 답변 토글 (`auto_reply_enabled`, `auto_reply_delay_min`)

**제외**:
- OCR/번역 파이프라인, 번역기 페이지
- 관리자 페이지, 인증, 악성댓글 필터링

### Phase 2

**핵심 추가**:
- **고서 번역기 (SFR-200, 파이프라인 정식 진입점)**
  - OCR 엔진 인터페이스/구현 (PaddleOCR + Google Vision)
  - 번역 엔진 인터페이스/구현 (Gemini + Claude)
  - `/translate` 페이지
- 후처리 파이프라인 단계 (요약/키워드/빈도수, 참고자료 추천)
- 번역 결과 사용자 수정 (직역/의역 인라인 편집, 수정 이력 저장)
- 번역 결과 저장/공유 (`/translate/:id`)
- **게시판-파이프라인 연동 (SFR-205)**: `board.pipeline_enabled=true`인 게시판의 자동 답변이 번역기 파이프라인을 재사용

**검토**:
- 작업 큐 도입 여부 (Celery/RQ)
- 파일 스토리지 외부화 (S3 호환)

### Phase 3

**추가**:
- `apps/admin` 신설
- 게시판 CRUD 및 설정 편집 UI (SFR-300)
- 사용자 인증/회원 시스템 (SFR-302)
- 악성댓글 AI 필터링 스케줄러 (SFR-301)

**구조 변화**:
- `users` 테이블 추가 (Posts/Comments에 FK 연결)
- Comments에 필터링 컬럼 추가
- 권한 미들웨어 도입

---

## 14. 변경 이력

| 날짜 | 버전 | 변경 내용 | 작성자 |
|------|------|----------|--------|
| 2026-04-09 | v1.0 | 초안 작성 (PRD/SRS 기반) | - |
| 2026-04-13 | v1.1 | PRD/SRS 정합성 보정: admin 게시글 관리, SFR-201/204 반영, NFR 매핑 섹션 추가, AD-08 추가, 클라우드 배포 Phase 명시 | - |
| 2026-04-13 | v1.2 | 파이프라인 흐름 재정의: 다중 게시판 도입(SFR-105), SFR-102/103 통합(→SFR-200/205), Phase 1 자동답변 텍스트 기반으로 명확화, 번역기를 파이프라인 정식 진입점으로 승격, 게시판별 설정(board.pipeline_enabled) 기반 파이프라인 재사용, §7.4 게시판 유형별 렌더링 추가 | - |
| 2026-04-13 | v1.3 | 파일 처리 구조 분리: `file` 테이블 + `file_map` 다형 매핑 도입, 파일 선업로드 후 글 작성 시 file_id 전달 흐름으로 §4.1 개정. SFR-104 조건을 "댓글 0건"으로 정정 (§4.2/§4.3) | - |
