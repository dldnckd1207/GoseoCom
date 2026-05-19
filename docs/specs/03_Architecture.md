# Architecture (시스템 아키텍처)

---

| 항목 | 내용 |
|------|------|
| **제품명** | Haedok AI (解讀 AI) |
| **버전** | v1.4.1 |
| **작성일** | 2026-04-09 (v1.0), 2026-04-13 (v1.1~v1.4 개정) |
| **작성자** | - |
| **관련 문서** | [PRD v1.1](01_PRD.md), [SRS v1.2](02_SRS.md) |

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
| **HTTP Method 컨벤션** | 생성/조회는 `POST`, 수정은 `PUT`, 삭제는 `DELETE`로 통일한다. `GET`은 Query String이 필요 없는 경우(경로 파라미터만으로 충분한 단건 조회, 파일 서빙 등)에 한해 허용한다. `PATCH`는 사용하지 않는다. |

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
└──────────────┬─────────────────────────┼────────────────────────┘
               │                         │
               │ External API    SQL ─────┘
               │                 │
        ┌──────▼─────────┐  ┌────▼──────────────┐  ┌────────────────────┐
        │  Google Vision │  │   PostgreSQL 16   │  │   File Storage     │
        │  Gemini Flash  │  │                   │  │   (Local Volume)   │
        │  Claude Haiku  │  │   (Docker)        │  │   업로드 이미지 저장  │
        │  Google OAuth  │  └───────────────────┘  └────────────────────┘
        │  Kakao OAuth   │
        └────────────────┘
```

### 3.2 컴포넌트 책임

| 컴포넌트 | 책임 | Phase |
|---------|------|-------|
| `apps/client` | 다중 게시판 UI(Phase 1 LIST, Phase 2 IMAGE/QNA 추가), 번역기(Phase 1 이미지 1장, Phase 2 PDF), 라이브러리, OAuth 로그인 | 1~ |
| `apps/admin` | 관리자 UI (게시판/게시글/댓글/사용자 관리, 로그 뷰어). 디렉토리 스캐폴드는 Phase 1, 구현은 Phase 3 | 3 |
| `apps/server` API Layer | HTTP 요청 처리, 입력 검증(Pydantic), 응답 직렬화, OAuth 콜백 처리, 권한 데코레이터 | 1~ |
| `apps/server` Service Layer | 비즈니스 로직, 트랜잭션 경계, 파이프라인 트리거, 인증 토큰 발급/검증 | 1~ |
| `apps/server` Repository Layer | DB 접근 추상화 (SQLAlchemy) | 1~ |
| AI Pipeline | OCR → 번역 → 후처리. Phase 1: 이미지 1장 (번역기 정식 진입점). Phase 2: PDF 다중 페이지 + 요약/키워드/빈도수, 게시판 자동답변 재사용 | 1~ |
| Scheduler | 주기적 작업. Phase 1: 텍스트 기반 자동 답변. Phase 2+: 파이프라인 연동 자동 답변. Phase 3: 악성댓글 검수 | 1~ |
| PostgreSQL | users/user_oauth/boards/posts/comments/file/file_map/books/book_pages/pipeline_runs/login_log/admin_audit_log/page_revisions 영속 저장 | 1~ |
| File Storage | 업로드 파일 바이너리 저장 (Phase 1 로컬 볼륨, 이후 S3 호환 검토) | 1~ |

### 3.3 외부 의존성

#### 외부 API (네트워크 호출, 장애 시 서비스 영향)

| 의존성 | 용도 | 추상화 위치 |
|--------|------|-------------|
| Google Vision API | OCR 텍스트 추출 (2순위) | `pipeline/ocr/GoogleVisionEngine` |
| Gemini Flash API | AI 번역/자동답변 (1순위) | `pipeline/translator/GeminiTranslator` |
| Claude Haiku API | AI 번역/자동답변 (2순위) | `pipeline/translator/ClaudeTranslator` |
| Google OAuth | 소셜 로그인 인증 (Phase 1~) | `app/core/oauth/GoogleOAuthClient` |
| Kakao OAuth | 소셜 로그인 인증 (Phase 1~) | `app/core/oauth/KakaoOAuthClient` |

#### 로컬 라이브러리 (프로세스 내 임베드, 설치/호환 이슈)

| 의존성 | 용도 | 추상화 위치 | 비고 |
|--------|------|-------------|------|
| PaddleOCR | OCR 텍스트 추출 (GPU 확보 후) | `pipeline/ocr/PaddleOcrEngine` | GPU 서버 확보 후 활성화. Phase 1은 Google Vision 사용 (AD-08) |
| kiwipiepy | 형태소 분석 기반 키워드 추출 및 단어 빈도수 계산 (Phase 2~) | `pipeline/postprocess/KeywordExtractor` | LLM 미호출, 로컬 처리로 비용/지연 절감 (AD-13) |

---

## 4. 데이터 흐름

> **참고**:
> - Phase 1부터 OAuth 인증이 적용된다. 비로그인 사용자는 게시글 읽기와 공유 링크 열람만 가능.
> - Phase 1부터 **번역기 파이프라인(이미지 1장)**이 존재한다. <br />게시판 자동 답변은 Phase 1에서는 텍스트만 사용하고, Phase 2에서 설정(`pipeline_enabled`) ON인 게시판에 한해 파이프라인을 재사용한다.
> - 본 섹션의 API 경로는 흐름 설명용 예시이며, 정식 API 설계 시 변경될 수 있다.

### 4.0 OAuth 로그인 (SFR-108, Phase 1)

```
[Client]                [API Layer]              [Provider]         [DB]
   |                        |                        |                |
   |-- GET /auth/:provider ─>| (redirect URL 생성)    |                |
   |<-- 302 redirect ───────|                        |                |
   |-- (provider 로그인 화면)────────────────────────>|                |
   |<-- callback?code=... ───────────────────────────|                |
   |-- GET /auth/:provider/callback?code=...────────>|                |
   |                        |-- exchange code ───────>|                |
   |                        |<-- access_token,       |                |
   |                        |    user profile ───────|                |
   |                        |   (email, provider_user_id,             |
   |                        |    name, profile_image_url)             |
   |                        |-- UPSERT users ────────────────────────>|
   |                        |   (email 기준, 없으면 INSERT             |
   |                        |    있으면 last_login_at 등 UPDATE)       |
   |                        |-- UPSERT user_oauth ───────────────────>|
   |                        |   (provider + provider_user_id 기준     |
   |                        |    없으면 INSERT, 있으면 UPDATE)         |
   |                        |-- INSERT login_log ───────────────────-->|
   |                        |-- JWT 발급             |                |
   |                        |<-- Set-Cookie(session) |                |
   |<-- 302 redirect (/) ───|                        |                |
```

**특징**:
- 같은 이메일이 다른 provider로도 로그인 가능 (users 1건 + user_oauth N건)
- 최초 로그인 시 `INITIAL_ADMIN_EMAILS` 목록에 포함되면 `user_level=100` 자동 승격 (Phase 3 활성화)



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
   |                        |-- save comment ───────────────────────>|
   |                        |   user_id = USER_00000000 (AI 시드)    |
   |                        |-- update auto_reply_status=completed ──>|
```

**특징**:
- 이미지 첨부 여부와 무관하게 **텍스트만** AI에 전달
- 게시판별 `auto_reply_delay_min` 설정 사용 (기본 5분)
- AI 댓글 여부는 `is_ai_gen` 파생 필드로 판별: `comment.user_id == 'USER_00000000'` (AD-07 참조)

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
   |                        |-- save comment ────────────────────────────────>|
   |                        |   user_id = USER_00000000 (AI 시드)             |
   |                        |-- update auto_reply_status=completed ─────────>|
```

**특징**:
- `pipeline_enabled=false`인 게시판은 §4.2 경로 유지
- `pipeline_enabled=true`인 게시판만 본 경로 실행
- 파이프라인 모듈은 §4.4 번역기와 동일 구현을 재사용
- AI 댓글 여부는 `is_ai_gen` 파생 필드로 판별: `comment.user_id == 'USER_00000000'` (AD-07 참조)

### 4.4 고서 번역기 (SFR-106, Phase 1 — 파이프라인 정식 진입점 / SFR-200 Phase 2에서 PDF 확장)

```
[Client]                [API Layer]        [Service]         [Pipeline]        [DB]
   |                        |                  |                  |              |
   |-- POST /translate ────>|                  |                  |              |
   |  (image)               |                  |                  |              |
   |                        |-- create book ──>|                  |              |
   |                        |                  |-- INSERT books (status=pending)>|
   |                        |<-- book_id ──────|                  |              |
   |<-- 202 Accepted -------|                  |                  |              |
   |    { book_id }         |                  |                  |              |
   |                        |                  |-- [BackgroundTask]              |
   |                        |                  |-- UPDATE status=ocr_processing >|
   |                        |                  |-- OCR ──────────>|              |
   |                        |                  |-- UPDATE status=translating ───>|
   |                        |                  |-- Translate ─────>|              |
   |                        |                  |-- UPDATE status=completed ─────>|
   |                        |                  |   (ocr_text, literal, interpretive 저장)
   |                        |                  |                  |              |
   |-- (폴링) GET /books/:id >|                  |                  |              |
   |<-- { status, result } ─|                  |                  |              |
```

**특징**:
- 파이프라인은 비동기(`BackgroundTasks`) 실행, 즉시 `book_id` 반환 (202 Accepted)
- `books.status` 단계: `pending → ocr_processing → translating → completed | failed`
- 클라이언트는 2~3초 간격 폴링으로 status 확인, 단계별 진행 메시지 표시
- Phase 2(다중 페이지) 착수 시 SSE 전환 검토 — 폴링으로 계속 운영도 가능

### 4.5 번역 결과 수정 (SFR-201, Phase 2)

```
[Client]                [API Layer]        [Service]         [DB]
   |                        |                  |               |
   |-- PUT /translations/:id ──>|              |               |
   |  (literal, interpretive)   |              |               |
   |                        | @require_level   |               |
   |                        | (UserRole.USER)  |               |
   |                        |-- update_translation ─>|          |
   |                        |                  |-- load book_page ─>|
   |                        |                  |-- 본인 소유 검증    |
   |                        |                  |   (book.owner_user_id == 요청자)
   |                        |                  |   └ 불일치 시 403 반환
   |                        |                  |-- save revision ──>| (page_revisions)
   |                        |                  |-- update book_page ─>|
   |                        |<-- updated ──────|               |
   |<-- 200 OK -------------|                  |               |
```

- **레벨 체크** (`@require_level(UserRole.USER)`): API Layer 데코레이터, 비로그인/GUEST 차단
- **소유 검증** (`book.owner_user_id == 요청자`): Service Layer, 타인 소유 Book 수정 차단 (403)
- 수정 이력은 `page_revisions` 테이블에 append-only 저장하여 원본 복구 가능

### 4.6 악성댓글 필터링 (SFR-301, Phase 3)

```
[Scheduler]              [Service]              [Pipeline]           [DB]
   |                        |                       |                  |
   |-- tick (configurable) >|                       |                  |
   |                        |-- find unchecked comments ─────────────>|
   |                        |   WHERE filtered_at IS NULL              |
   |                        |     AND del_yn = false                   |
   |                        |<-- comment[] ──────────────────────────|
   |                        |-- for each comment ──>|                  |
   |                        |                       |-- AI judge (Gemini)
   |                        |                       |<-- malicious: bool, reason
   |                        |-- UPDATE comments ───────────────────────>|
   |                        |   is_filtered = true (악성인 경우)        |
   |                        |   filter_reason = AI 판별 사유            |
   |                        |   filtered_at = now()                    |
```

**표시 UX**:
- `is_filtered=true` 댓글은 **삭제되지 않음**. 화면에 "AI가 감지한 악성 댓글입니다" 메시지와 함께 "내용 보기" 버튼 표시
- 사용자가 "내용 보기" 클릭 시 원본 댓글 내용 열람 가능
- 관리자는 필터 해제 가능 (`is_filtered=false`, `filter_reviewed_by` 기록)

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

도메인 기반 모듈 구조를 채택한다. 각 도메인은 router, service, repository, domain을 자체적으로 포함한다.

| 모듈 | 책임 |
|------|------|
| `app/core/user/` | users, user_oauth ORM 모델, 사용자 서비스/레포지토리 |
| `app/core/settings/` | 환경변수, 앱 설정 (Settings) |
| `app/core/common/` | DB 연결, 공통 예외, 로깅, 데코레이터 모음 (`@require_level` 등) |
| `app/core/files/` | file/file_map ORM 모델, 스토리지 추상화 (로컬/S3 호환) |
| `app/core/audit/` | admin_audit_log ORM 모델 및 서비스 (Phase 3) |
| `app/auth/` | OAuth 클라이언트 (Google/Kakao), JWT 발급/검증, 로그인 흐름, login_log |
| `app/board/` | boards, posts, comments 도메인. router.py (일반) + admin_router.py (관리자, Phase 3) |
| `app/translate/` | books, book_pages, page_revisions 도메인 + pipeline (OCR/번역 엔진). router.py + admin_router.py (Phase 3) |
| `app/scheduler/` | 주기적 작업 — board 자동 답변, translate 파이프라인, 악성댓글 필터링 (APScheduler 등) |
| `app/main.py` | FastAPI 앱 부트스트랩, 라우터 등록, 미들웨어 설정 |

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

> **파이프라인은 Phase 1부터 도입된다.** Phase 1은 이미지 1장 단건 번역(SFR-106)으로 시작하고, Phase 2에서 PDF 다중 페이지(SFR-200)로 확장된다.
>
> **정식 진입점**: 고서 번역기(SFR-106, Phase 1 / SFR-200 Phase 2 확장). 사용자가 이미지·PDF를 직접 입력하는 `/translate` 페이지가 파이프라인을 사용하는 1차 경로.
>
> **재사용처**: 게시판 자동 답변(SFR-205, Phase 2). 게시판 설정 `pipeline_enabled=true`일 때만 동일 파이프라인 모듈을 재호출.

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

| 인터페이스 | Phase 1 | GPU 확보 후 | 전환 방법 |
|-----------|---------|------------|----------|
| `OcrEngine` | `GoogleVisionEngine` (외부 API) | `PaddleOcrEngine` (로컬 임베드) | 환경변수 `OCR_ENGINE=google_vision\|paddle` |
| `Translator` | `GeminiTranslator` | `ClaudeTranslator` (폴백) | 환경변수 `TRANSLATOR_ENGINE=gemini\|claude` |

엔진 선택은 환경 변수/Settings로 주입한다. 코드 변경 없이 설정만으로 전환 가능하며, 런타임 동적 전환은 Phase 1 범위 외이다.

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

| Phase | 실행 방식 | 진행도 표시 | 비고 |
|-------|----------|------------|------|
| Phase 1 | FastAPI `BackgroundTasks` | 클라이언트 폴링 (`books.status` 단계별 조회) | 단순함 우선, 단일 인스턴스 가정 |
| Phase 2 | 동일 (필요 시 작업 큐 검토) | SSE 전환 검토 (다중 페이지 페이지별 진행도), 폴링 유지도 가능 | 부하/장애 격리 필요 시 Celery/RQ 도입 |
| Phase 3 | 작업 큐 권장 | SSE 또는 폴링 | 관리자 페이지에서 재실행/재시도 필요 |

---

## 7. 프론트엔드 아키텍처 (apps/client)

### 7.1 라우팅 (Remix)

> `/auth/*` 경로는 Remix 라우트가 아니다. nginx가 FastAPI로 프록시하며, Remix 로그인 버튼은 해당 FastAPI URL로 단순 이동한다.

| 경로 | 화면 | Phase |
|------|------|-------|
| `/` | 홈 (게시판 목록 또는 기본 게시판으로 리다이렉트) | 1 |
| `/community` | 커뮤니티 (전체/게시판 탭, 동적 렌더링) | 1 |
| `/community/:code` | 게시판 상세 (LIST Phase 1 / IMAGE/QNA Phase 2) | 1 |
| `/community/:code/posts/new` | 게시글 작성 (로그인 필수) | 1 |
| `/community/:code/posts/:id` | 게시글 상세 (댓글 포함) | 1 |
| `/community/:code/posts/:id/edit` | 게시글 수정 (본인/관리자) | 1 |
| `/translate` | 번역기 페이지 (이미지 1장, 로그인 필수) | 1 |
| `/library` | 라이브러리 (내 Book 이력, 로그인 필수) | 1 |
| `/books/:id` | Book 상세 (owner 전용) | 1 |
| `/s/:share_token` | 공유 링크 (열람 전용, 비로그인 가능) | 2 |

### 7.2 데이터 로딩

- Remix `loader`로 서버 데이터 페칭
- 변형은 `action` 사용 (게시글 작성/수정/삭제)
- 클라이언트 상태는 React state 위주, 전역 상태 라이브러리는 미도입

### 7.3 파이프라인 결과 표시

**번역기 진행 상태 표시**
- 이미지 업로드 후 `books.status`를 2~3초 간격 폴링
- status 값에 따라 단계별 메시지 표시:
  - `pending` → "번역 준비 중..."
  - `ocr_processing` → "문자 인식 중..."
  - `translating` → "번역 중..."
  - `completed` → 직역/의역 결과 렌더링
  - `failed` → 오류 메시지 표시
- 번역 완료 후 직역/의역 나란히 비교 가능한 레이아웃으로 표시
- Phase 2(다중 페이지) 착수 시 SSE 전환 검토

**게시판 AI 자동 답변**
- 게시글 상세 페이지에서 댓글 목록 폴링 (Phase 1: 2~3초 간격)
- `is_ai_gen=true` 댓글은 "해독이(가칭)" 에이전트 답변으로 구분 표시

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

파일 경로는 DB(`file.storage_path`)에만 저장하고, 백엔드는 `core/files/` 스토리지 추상화를 통해 접근한다. 엔티티(게시글/댓글 등)와의 연결은 `file_map`(다형 매핑 테이블)으로 관리한다.

**파일 업로드 / 접근 흐름**

| 작업 | 방식 |
|------|------|
| 업로드 | `POST /files` (multipart) → `file` 레코드 생성 → `file_id` 반환 |
| 접근 | `GET /files/:id` → FastAPI가 `file.storage_path` 기반으로 파일 응답 (Phase 1) |
| Phase 2+ | 동일 URL 유지, 내부 구현만 S3 presigned URL 또는 nginx X-Accel-Redirect로 전환 가능 |

클라이언트는 항상 `GET /files/:id`만 호출하며, 실제 서빙 방식은 Phase에 따라 내부적으로 변경된다.

---

## 9. 비기능 요구사항 매핑 (NFR)

SRS §8의 비기능 요구사항을 아키텍처상에서 어떻게 달성하는지 매핑한다.

### 9.1 성능

| NFR | 목표 | 달성 전략 |
|-----|------|----------|
| OCR + 번역 파이프라인 | 30초 이내 (A4 1페이지) | BackgroundTasks 비동기 실행, 엔진별 타임아웃 설정, 이미지 리사이즈 전처리. Phase 1은 Google Vision API 응답 속도에 의존 |
| 게시판 API 응답 | 500ms 이내 | Repository 단일 쿼리 기준, N+1 회피, 목록은 페이지네이션 + 인덱스 |
| 이미지 업로드 | 최대 10MB | API Layer에서 Content-Length/파일 크기 사전 검증 |

### 9.2 보안

| NFR | 대응 위치 | 구현 방식 |
|-----|----------|----------|
| 파일 업로드 검증 | `app/core/files/` (업로드 라우터) | MIME 타입 화이트리스트(image/*), 크기 제한 10MB, 확장자 검증 |
| XSS | `apps/client`, `apps/admin` | React의 기본 이스케이핑 + `dangerouslySetInnerHTML` 금지 정책, CSP 헤더 |
| SQL Injection | `app/*/repository.py` | SQLAlchemy ORM + 파라미터 바인딩 (raw SQL 금지) |
| CORS | `app/main.py` | FastAPI CORS 미들웨어, 허용 오리진 `core/settings/`로 주입 |
| 입력 검증 | `app/*/router.py` | Pydantic RequestSchema 필수 |
| JWT / 인증 토큰 | `app/auth/` | JWT `httpOnly` 쿠키 저장 (XSS 방어), 토큰 만료 시간 설정 (`core/settings/`로 관리) |

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
│   ├── client/              # React / Remix (FSD 구조)
│   │   ├── app/
│   │   │   ├── routes/      # Remix 파일 기반 라우팅
│   │   │   │   ├── _index.tsx
│   │   │   │   ├── board/
│   │   │   │   ├── translate/
│   │   │   │   ├── library/
│   │   │   │   └── books/
│   │   │   ├── widgets/     # 독립적인 대형 UI 블록 (BoardList, TranslatePanel 등)
│   │   │   ├── features/    # 사용자 인터랙션 단위 (CreatePost, UploadImage 등)
│   │   │   ├── entities/    # 비즈니스 엔티티 UI (Post, Board, Book, Comment 등)
│   │   │   ├── shared/      # 공통 UI 컴포넌트, API 클라이언트, 유틸
│   │   │   └── root.tsx
│   │   ├── public/
│   │   ├── package.json
│   │   └── ...
│   ├── server/              # FastAPI
│   │   ├── app/
│   │   │   ├── core/
│   │   │   │   ├── user/        # users, user_oauth
│   │   │   │   ├── settings/    # 환경변수, 앱 설정
│   │   │   │   ├── common/      # DB, 예외, 로깅, decorators
│   │   │   │   ├── files/       # file/file_map, 스토리지 추상화
│   │   │   │   └── audit/       # admin_audit_log (Phase 3)
│   │   │   ├── auth/            # OAuth, JWT, login_log
│   │   │   ├── board/           # boards, posts, comments
│   │   │   │   ├── router.py
│   │   │   │   ├── admin_router.py  # Phase 3
│   │   │   │   ├── service.py
│   │   │   │   ├── repository.py
│   │   │   │   └── domain.py
│   │   │   ├── translate/       # books, book_pages, pipeline
│   │   │   │   ├── router.py
│   │   │   │   ├── admin_router.py  # Phase 3
│   │   │   │   ├── service.py
│   │   │   │   ├── repository.py
│   │   │   │   ├── domain.py
│   │   │   │   └── pipeline/
│   │   │   │       ├── ocr/
│   │   │   │       └── translator/
│   │   │   ├── scheduler/
│   │   │   └── main.py
│   │   ├── alembic/
│   │   ├── tests/           # 도메인 구조 미러링
│   │   │   ├── core/
│   │   │   ├── auth/
│   │   │   ├── board/
│   │   │   ├── translate/
│   │   │   └── scheduler/
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

nginx 없이 각 앱을 직접 포트로 실행한다. OAuth callback URL도 포트 포함(`http://localhost:8000/auth/google/callback`)으로 Provider에 등록한다.

```
[Developer Machine]
  ├─ apps/client     (npm run dev, port 3000)
  ├─ apps/server     (uv run uvicorn, port 8000)
  └─ Docker Compose
       └─ postgres:16        (port 5432)
```

### 11.2 Docker Compose 통합 실행 (운영/배포)

nginx를 reverse proxy로 두어 단일 도메인으로 client와 server를 통합한다. OAuth `client_secret`은 server 환경변수에만 존재하며, OAuth 흐름 전체(redirect 생성 → callback 수신 → token 교환 → JWT 발급)를 FastAPI가 처리한다.

```
[Host]
  └─ Docker Compose
       ├─ nginx       (port 80/443, reverse proxy)
       │    ├─ /auth/*   →  server:8000   (OAuth 흐름)
       │    ├─ /api/*    →  server:8000   (REST API)
       │    └─ /*        →  client:3000   (Remix)
       ├─ client      (Remix build, port 3000)
       ├─ server      (FastAPI + Pipeline + Scheduler, port 8000)
       ├─ postgres
       └─ volumes
            └─ uploads/    (이미지 저장)
```

OAuth Provider에 등록하는 callback URL: `https://domain.com/auth/google/callback`

### 11.3 클라우드 배포

| Phase | 방식 | 비고 |
|-------|------|------|
| Phase 1 | 단일 호스트 Docker Compose + nginx | 개발/데모 용도, 로컬 볼륨 사용 |
| Phase 2 | 단일 호스트 Docker Compose 유지 | 파일 스토리지 S3 호환 이전 검토 (§8.2) |
| Phase 3 | 운영 토폴로지 확정 | server 인스턴스 분리, PostgreSQL 매니지드 DB 이전, `apps/admin` 별도 배포 단위 및 nginx 라우팅 추가 검토 |

정확한 운영 토폴로지(호스트 스펙, 리전, 보안 그룹)는 Phase 3 배포 착수 시점에 별도 배포 계획서로 확정한다.

---

## 12. 핵심 설계 결정 (ADR Lite)

| ID | 결정 | 이유 | 트레이드오프 |
|----|------|------|--------------|
| **AD-01** | 모노레포 채택 | 3명이 병렬 개발하면서 문서/타입/마이그레이션을 한 저장소에서 추적 | 빌드/CI 복잡도 증가 |
| **AD-02** | OCR/번역 엔진 추상화 | 1순위 무료 엔진으로 시작, 품질 부족 시 2순위로 전환 | 인터페이스 설계 비용 |
| **AD-03** | 단일 FastAPI 백엔드 | API + 파이프라인 + 스케줄러를 한 서비스에 통합 (초기 단순함) | 향후 분리 시 리팩토링 비용 |
| **AD-04** | PostgreSQL 단일 DB | 관계형 데이터 + 향후 검색(pg_trgm, FTS) 확장 가능 | 검색 특화 시 별도 엔진(예: Elasticsearch) 필요 가능 |
| ~~**AD-05**~~ | ~~Phase 1 비인증~~ | **AD-09로 대체됨** (Phase 1부터 OAuth 적용) | — |
| **AD-06** | 파이프라인 BackgroundTasks (Phase 1) | 별도 큐 인프라 없이 비동기 실행 | 단일 인스턴스 가정, 장애 격리 약함 |
| **AD-07** | AI 댓글은 단일 시드 계정(`USER_00000000`, "해독이(가칭)")으로 통합. `is_ai_gen` 파생 필드(`user_id == 'USER_00000000'`)로 구분 | 텍스트/파이프라인 방식 모두 동일 AI 에이전트 정체성으로 표시. `comments` 테이블에 별도 컬럼 불필요 | 자동 답변 방식(텍스트 vs 파이프라인) 구분은 `pipeline_runs` 테이블로만 추적 가능 |
| **AD-08** | Phase 1 OCR은 Google Vision API 사용 (GPU 서버 미확보). GPU 확보 후 PaddleOCR 로컬 임베드로 전환. 전환은 환경변수(`OCR_ENGINE`)로만 처리, 코드 변경 없음 | Phase 1 빠른 개발 착수. PaddleOCR 임베드 시 서버 메모리 점유 증가 및 기동 지연 회피 | GPU 확보 전까지 Google Vision API 비용 발생. PaddleOCR 전환 후 별도 컨테이너 분리 검토 필요 |
| **AD-09** | 인증은 Phase 1부터 OAuth(Google + Kakao). LOCAL 로그인 미지원 | 개인정보 최소 수집(이메일/이름/프로필 사진만). 비인증 상태 혼란 없이 권한 모델 일관성 확보 | OAuth Provider 장애 시 로그인 불가. Phase 3에서 필요 시 LOCAL 확장 가능한 구조로 설계 |
| **AD-10** | 번역 단위는 `Book` + `book_pages` (다중 페이지 컨테이너) | Phase 1은 1 Book = 1 Page(Quick)로 시작, Phase 2에 PDF(N Page) 자연스럽게 확장. 마이그레이션 없음 | 단건 조회에도 JOIN 1단계 추가 |
| **AD-11** | 파일은 `file` + `file_map`(다형 매핑). 업로드 API와 엔티티 생성 API 분리 | Post, Comment, BookPage 등 다양한 엔티티가 동일 파일 테이블 재사용. 프론트에서 업로드/글작성 분리로 UX 개선 | 매핑 조회 시 간접 JOIN |
| **AD-12** | 권한은 `user_level` 정수 레벨(enum 상수 래핑) + 데코레이터 체크 | 중간 레벨 추가 용이, 코드 가독성 확보 | 매직 넘버 위험(enum으로 방어) |
| **AD-13** | 키워드/빈도수는 `kiwipiepy` 로컬, 요약만 LLM | LLM 호출 비용/지연 절감. 단순 형태소 분석은 로컬로 충분 | `kiwipiepy` 설치/호환 이슈 가능 |
| **AD-14** | 시연/운영 시점에 외부 API 레이트 리밋·장애 리스크 회피가 필요하면 L40S GPU + vLLM 자체 호스팅 번역 엔진을 보조로 도입 | 엔진 추상화 덕에 새 구현체 하나 추가로 통합. 데이터 프라이버시/비용 제어 | GPU 비용 및 모델 로드 오버헤드. 평시에는 비활성 |
| **AD-15** | 백엔드는 레이어 기반이 아닌 도메인 기반 모듈 구조 채택 (`core/`, `auth/`, `board/`, `translate/`) | 3명 병렬 개발 시 도메인별 파일 충돌 최소화. 기능 추가/변경 시 영향 범위 명확. Phase별 도메인 독립 확장 가능 | 도메인 간 공유 모델은 `core/`로 별도 관리 필요 |
| **AD-16** | 프론트엔드는 FSD(Feature-Sliced Design) 구조 채택 (`widgets/` → `features/` → `entities/` → `shared/`) | 관심사 분리 명확, 팀원 간 작업 범위 충돌 최소화. Remix 파일 기반 라우팅(`routes/`)과 병행 적용 | Remix 초기 학습 비용 + FSD 구조 설계 비용 중복 |
| **AD-17** | HTTP Method 컨벤션: 생성/조회 `POST`, 수정 `PUT`, 삭제 `DELETE`. `GET`은 QS가 필요 없는 경우(경로 파라미터만으로 충분한 단건 조회, 파일 서빙 등)에 한해 허용. `PATCH` 미사용 | QS(Query String) 노출 방지, 보안 강화. `PUT`으로 통일하여 부분/전체 수정 혼용 방지 | `PUT`은 리소스 전체 교체 의미이므로 요청 시 전체 필드 전달 필요 |
| **AD-18** | 운영 환경에 nginx reverse proxy 도입. `/auth/*` · 비 `/api/*` 경로 분기 처리 | OAuth `client_secret`을 FastAPI 환경변수에만 격리. 단일 도메인으로 CORS 불필요. OAuth callback URL 깔끔하게 유지 | nginx 설정 파일 관리 추가. 로컬 개발은 직접 포트 접근으로 nginx 불필요 |

---

## 13. Phase별 아키텍처 변화

### Phase 1 (MVP)

**구성**: `apps/client` + `apps/server` + PostgreSQL (+ `apps/admin` 스캐폴드)

**핵심 컴포넌트**:
- OAuth 로그인 (Google + Kakao, SFR-108) — `users` + `user_oauth` 분리, FastAPI 처리, nginx `/auth/*` 프록시
- 권한 체계 스키마 (`user_level`) — `USER` 레벨까지만 데코레이터 활성
- 다중 게시판 (SFR-105) — `boards` 테이블, `board_type`(LIST/IMAGE/QNA 컬럼), Phase 1은 LIST UI만
- 게시글/댓글 CRUD (SFR-101) — `posts`, `comments` (작성자 FK)
- 파일 업로드 분리 구조 (`file` + `file_map` 다형 매핑) — 선업로드 → 매핑
- 고서 번역기 (SFR-106) — 이미지 1장, **OCR: Google Vision API**, AI 번역: Gemini Flash, **파이프라인 정식 진입점**
- 번역 진행 상태 표시 — `books.status` 폴링 (pending → ocr_processing → translating → completed)
- 라이브러리 (SFR-107) — 단순 리스트, 본인 Book 조회
- AI 자동 답변 (SFR-104) — 텍스트 기반, 댓글 0건 + 시간 경과 조건, `board.auto_reply_*`
- 로그 스키마 선반영: `login_log`(Phase 1부터 INSERT), `admin_audit_log`(스키마만)
- AI 시드 계정: `USER_00000000` ("해독이(가칭)", Phase 1 투입 — 텍스트/파이프라인 자동 답변 공통 사용)
- `comments` 필터링 컬럼 선반영 (`is_filtered` 등, Phase 3에서 활용)

**제외**:
- PDF 다중 페이지, USER_CREATED Book, 요약/키워드/빈도수
- 게시판-파이프라인 연동 자동 답변
- IMAGE/QNA 유형 UI, 라이브러리 탭/즐겨찾기/제목 검색
- 관리자 페이지 구현, 악성댓글 필터링

### Phase 2

**핵심 추가**:
- 고서 번역기 확장 (SFR-200) — PDF 다중 페이지(100p/50MB), `book_type='USER_CREATED'`
- 후처리 파이프라인 단계 (SFR-202) — 요약(LLM) + 키워드/빈도수(kiwipiepy 로컬)
- 번역 결과 수정 (SFR-201, 본인만) — `page_revisions` 이력
- 번역 결과 공유 (SFR-203) — `books.share_token`, `/s/:token`, 열람 전용, OFF 기본
- 게시판-파이프라인 연동 자동 답변 (SFR-205) — `board.pipeline_enabled=true` 필터
- 라이브러리 확장 (SFR-206) — 탭/즐겨찾기/제목 검색
- 게시판 IMAGE/QNA 유형 UI 추가

**검토**:
- 작업 큐 도입 여부 (Celery/RQ)
- 파일 스토리지 외부화 (S3 호환)

### Phase 3

**추가**:
- 관리자 페이지 (SFR-300, 1차 표준) — `apps/admin` 구현 완료
- 권한 데코레이터 활성화 (SFR-302) — ADMIN/SYSTEM_ADMIN, 최초 관리자 부트스트랩
- 관리자 로그 뷰어 (SFR-303) — `login_log` 조회, `admin_audit_log` INSERT 시작 + 조회
- 악성댓글 AI 필터링 (SFR-301) — 배치 스케줄러, "내용 보기" 토글 UI
- 참고자료 추천 (SFR-304) — 구현 방식 착수 시 회의
- 타인 번역 제안 (SFR-305) — suggestion 플로우

**시간 여유 시 (2차 풀스펙)**:
- 시스템 로그 뷰어 (SYSTEM_ADMIN 전용)
- 파이프라인 재실행 UI, OCR/번역 엔진 전환 UI

---

## 14. 변경 이력

| 날짜 | 버전 | 변경 내용 | 작성자 |
|------|------|----------|--------|
| 2026-04-09 | v1.0 | 초안 작성 (PRD/SRS 기반) | - |
| 2026-04-13 | v1.1 | PRD/SRS 정합성 보정: admin 게시글 관리, SFR-201/204 반영, NFR 매핑 섹션 추가, AD-08 추가, 클라우드 배포 Phase 명시 | - |
| 2026-04-13 | v1.2 | 파이프라인 흐름 재정의: 다중 게시판 도입(SFR-105), SFR-102/103 통합(→SFR-200/205), Phase 1 자동답변 텍스트 기반으로 명확화, 번역기를 파이프라인 정식 진입점으로 승격, 게시판별 설정(board.pipeline_enabled) 기반 파이프라인 재사용, §7.4 게시판 유형별 렌더링 추가 | - |
| 2026-04-13 | v1.3 | 파일 처리 구조 분리: `file` 테이블 + `file_map` 다형 매핑 도입, 파일 선업로드 후 글 작성 시 file_id 전달 흐름으로 §4.1 개정. SFR-104 조건을 "댓글 0건"으로 정정 (§4.2/§4.3) | - |
| 2026-04-13 | v1.4 | prd-fix 전체 반영: OAuth(Google/Kakao) Phase 1 당김, OCR/번역 파이프라인 Phase 1 당김(이미지 1장 정식 진입점), 라이브러리(Quick) Phase 1, PDF/요약/수정/공유/탭+즐겨찾기 Phase 2, 관리자 페이지 1차 표준 Phase 3, 악성댓글 필터 UX 구체화, 로그 테이블 2종 선반영. §13 Phase 로드맵 전면 재작성. §4.0 OAuth 흐름 신규. §7.1 라우팅에 `/translate`·`/library`·`/s/:token` 반영. AD-09~AD-14 신규 | - |
| 2026-04-13 | v1.4.1 | 리뷰 보정: §6 도입부 "Phase 2 도입" 문구 → Phase 1 파이프라인 기술로 수정, §4.5 `translation_revisions` → `page_revisions` 명명 일치, AD-05 폐기 표시(AD-09로 대체), §4.2/§4.3 시퀀스에 AI 시드 계정 user_id 명시 (USER_00000000_AUTO / USER_00000000_PIPELINE) | - |
| 2026-04-14 | v1.5 | 전체 아키텍처 리뷰 반영: §2 HTTP Method 컨벤션 원칙 추가. §3.1 구성도 File Storage 화살표 추가. §3.3 외부 의존성 외부API/로컬라이브러리 분리, OAuth 항목 추가. §4.0 OAuth UPSERT 패턴으로 수정. §4.2/§4.3 AI 시드 계정 단일화(USER_00000000 "해독이(가칭)"), author_type 제거 → is_ai_gen 파생 필드로 대체. §4.4 번역기 비동기 전환(202 Accepted + books.status 폴링). §4.5 PATCH→PUT, 소유권 검증 단계 추가. §4.6 악성댓글 조건/저장 필드 보완, 마스킹 UX 명시. §5.2/§10 레이어→도메인 기반 모듈 구조 전환(core/auth/board/translate), FSD 프론트엔드 구조, tests 도메인 미러링. §6.2 Phase 1 OCR Google Vision 우선, PaddleOCR GPU 확보 후 전환, 환경변수 명시. §7.1 /auth/* 라우트 제거, /boards→/board. §7.3 번역 진행 상태/AI 댓글 표시 분리. §8.2 파일 서빙 흐름 추가. §9.1 Google Vision 레이턴시 의존 명시. §9.2 모듈 경로 업데이트, JWT httpOnly 항목 추가. §11 nginx reverse proxy 도입, 로컬개발 PaddleOCR 컨테이너 제거. AD-15~AD-18 신규 | - |
