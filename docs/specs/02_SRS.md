# SRS (Software Requirements Specification)

---

| 항목 | 내용 |
|------|------|
| **제품명** | Haedok AI (解讀 AI) |
| **버전** | v1.2.1 |
| **작성일** | 2026-04-02 (v1.0), 2026-04-13 (v1.2.1 개정) |
| **작성자** | - |
| **관련 문서** | [PRD](01_PRD.md), [Architecture](03_Architecture.md) |

---

## 1. 개요

### 1.1 목적

본 문서는 Haedok AI 시스템의 소프트웨어 요구사항을 정의한다. 각 기능별 요구사항을 고유번호로 관리하며, 시스템 구성, 기술 스택, 비기능 요구사항을 포함한다. 시스템 아키텍처, DB 설계, API 설계 등의 상세 내용은 별도 문서로 관리한다.

### 1.2 범위

Haedok AI는 크게 두 가지 핵심 시스템으로 구성된다:

- **고서 번역기**: 고서 이미지/텍스트를 입력받아 OCR + AI 번역 파이프라인을 통해 직역/의역 결과를 제공
- **커뮤니티 게시판**: 고서 관련 질문/토론 게시판으로, AI 자동 답변 및 악성댓글 필터링 기능 포함

### 1.3 Phase별 상세 문서

| Phase | 문서 | 상태 |
|-------|------|------|
| Phase 1 | [Phase 1 SRS](_srs/phase1.md) | 미작성 |
| Phase 2 | [Phase 2 SRS](_srs/phase2.md) | 미작성 |
| Phase 3 | [Phase 3 SRS](_srs/phase3.md) | 미작성 |

---

## 2. 시스템 구성 개요

### 2.1 전체 구성

```
┌─────────────────────────────────────────────────────────┐
│                        Client                           │
│                   (React / Remix)                        │
│              apps/client                                │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP (REST API)
┌──────────────────────▼──────────────────────────────────┐
│                       Server                            │
│                  (FastAPI / Python)                      │
│              apps/server                                │
│  ┌─────────┐ ┌──────────┐ ┌───────────┐ ┌───────────┐  │
│  │ API     │ │ Services │ │ Scheduler │ │ Pipeline  │  │
│  │ Layer   │ │ Layer    │ │           │ │ (OCR+AI)  │  │
│  └─────────┘ └──────────┘ └───────────┘ └───────────┘  │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│                    PostgreSQL                            │
└─────────────────────────────────────────────────────────┘
```

> 상세 아키텍처 설계는 별도 문서로 관리 예정

### 2.2 앱 구성

| 앱 | 역할 | 기술 | Phase |
|----|------|------|-------|
| `apps/client` | 사용자 웹 (다중 게시판 + 번역기 + 라이브러리 + OAuth 로그인) | React / Remix | Phase 1~ |
| `apps/server` | 백엔드 API + AI 파이프라인(Phase 1 이미지 단건, Phase 2 PDF 다중 페이지) + 스케줄러 | FastAPI (Python) | Phase 1~ |
| `apps/admin` | 관리자 페이지 (디렉토리만 Phase 1 준비, 구현은 Phase 3) | React / Remix | Phase 3 |

### 2.3 외부 서비스 의존성

| 서비스 | 용도 | 우선순위 |
|--------|------|----------|
| PaddleOCR | 고서 이미지 OCR 텍스트 추출 | 1순위 (기본) |
| Google Vision API | OCR 텍스트 추출 (PaddleOCR 대체) | 2순위 (인식률 부족 시) |
| Gemini Flash | AI 직역/의역 번역, 자동 답변, 악성댓글 필터링 | 1순위 (무료) |
| Claude Haiku | AI 번역 (Gemini 품질 부족 시) | 2순위 (유료) |

---

## 3. 기술 스택

| 영역 | 기술 | 버전 |
|------|------|------|
| Frontend | React / Remix | LTS |
| Backend | FastAPI (Python) | Python 3.12+ |
| Database | PostgreSQL | 16+ |
| Package Manager (Python) | uv | - |
| Package Manager (Node) | npm | LTS |
| Runtime | Node.js | LTS |
| 컨테이너 | Docker & Docker Compose | - |
| OAuth | Google OAuth 2.0 + Kakao OAuth 2.0 | - |
| 형태소 분석 (키워드/빈도수) | kiwipiepy | - |
| OCR | PaddleOCR (1순위), Google Vision API (2순위) | - |
| AI 번역/답변 | Gemini Flash (1순위, 무료), Claude Haiku (2순위) | - |

---

## 4. 요구사항 목록 총괄

### 4.1 요구사항 ID 규칙

- **SFR**: Software Functional Requirement (기능 요구사항)
- 번호 체계: `SFR-{Phase}{순번}` (예: SFR-101 = Phase 1의 첫 번째 요구사항)

### 4.2 전체 요구사항 목록

| 요구사항 ID | 기능명 | 대상 Phase | 우선순위 |
|------------|--------|-----------|----------|
| SFR-100 | 프로젝트 기반 구축 | Phase 1 | Must |
| SFR-101 | 게시판 CRUD (파일 업로드 분리 + file_map 매핑 포함) | Phase 1 | Must |
| ~~SFR-102~~ | ~~OCR 텍스트 추출~~ | ~~Phase 1~~ | **SFR-106에 흡수 (Phase 1, OCR 엔진 구현체 포함). SFR-200(Phase 2)에서 PDF 확장 시 재사용.** |
| ~~SFR-103~~ | ~~AI 자동 댓글 (파이프라인 결과)~~ | ~~Phase 1~~ | **SFR-205에 통합 (Phase 2로 이동)** |
| SFR-104 | AI 자동 답변 (텍스트 기반) | Phase 1 | Must |
| SFR-105 | 게시판 관리 (다중 게시판) | Phase 1 | Must |
| SFR-106 | 고서 번역기 (이미지 1장, 파이프라인 정식 진입점) | Phase 1 | Must |
| SFR-107 | 라이브러리 (내 번역 이력, 단순 리스트) | Phase 1 | Must |
| SFR-108 | 사용자 인증 (OAuth: Google + Kakao) | Phase 1 | Must |
| SFR-200 | 고서 번역 파이프라인 확장 (PDF 다중 페이지) | Phase 2 | Should |
| SFR-201 | 번역 결과 수정 (본인 소유만) | Phase 2 | Should |
| SFR-202 | 핵심 요약 / 키워드 / 빈도수 | Phase 2 | Should |
| SFR-203 | 결과 저장 / 공유 (공유 링크) | Phase 2 | Should |
| ~~SFR-204~~ | ~~참고자료 추천~~ | ~~Phase 2~~ | **Phase 3으로 이동 (구현 방식 미정)** |
| SFR-205 | 게시판 고서 파이프라인 자동 연동 | Phase 2 | Should |
| SFR-206 | 라이브러리 확장 (탭 구조 + 즐겨찾기 + 제목 검색) | Phase 2 | Should |
| SFR-300 | 관리자 페이지 (게시판/게시글/댓글/사용자 관리, 1차 표준) | Phase 3 | Should |
| SFR-301 | 악성댓글 AI 필터링 | Phase 3 | Could |
| SFR-302 | 사용자 권한 관리 (ADMIN/SYSTEM_ADMIN 데코레이터 활성화) | Phase 3 | Should |
| SFR-303 | 관리자 로그 뷰어 (login_log / admin_audit_log) | Phase 3 | Should |
| SFR-304 | 참고자료 추천 (Phase 2에서 이동) | Phase 3 | Could |
| SFR-305 | 타인 번역 제안 (suggestion) | Phase 3 | Could |

---

## 5. Phase 1 요구사항 상세

### SFR-100: 프로젝트 기반 구축

| 항목 | 내용 |
|------|------|
| **요구사항 고유번호** | SFR-100 |
| **요구사항 명칭** | 프로젝트 기반 구축 |
| **대상 Phase** | Phase 1 |
| **우선순위** | Must |

**정의**: 모노레포 구조의 프로젝트를 초기화하고, FastAPI + PostgreSQL 기반의 개발 환경을 구축한다.

**세부 내용**:
- 모노레포 구조 설정 (apps/client, apps/server, apps/admin)
- FastAPI 서버 구성
- PostgreSQL Docker Compose 구성
- uv 패키지 매니저 기반 의존성 관리
- React / Remix 클라이언트 프로젝트 초기화
- ID 채번 전략: 엔티티(게시판/게시글/댓글 등)는 문자열 ID-GEN(`BOARD_00000001` 형식), 로그/이력성 데이터(파이프라인 실행 로그 등)는 `BIGSERIAL` 적용

---

### SFR-101: 게시판 CRUD

| 항목 | 내용 |
|------|------|
| **요구사항 고유번호** | SFR-101 |
| **요구사항 명칭** | 게시판 CRUD |
| **대상 Phase** | Phase 1 |
| **우선순위** | Must |

**정의**: 게시글 작성, 조회, 수정, 삭제 기능을 제공하는 커뮤니티 게시판을 구현한다. 게시글은 다중 게시판(SFR-105) 중 하나에 귀속된다. 관리자 기능은 Phase 3에서 구현한다.

**세부 내용**:
- 게시글 작성 (제목, 본문, 소속 게시판 지정, 첨부 파일 ID 리스트)
- **파일 업로드는 선업로드 API (`POST /api/v1/boards/{board_code}/uploads`)로 분리** — 업로드 시 `file` 레코드 생성 후 `file_id` 반환
- 글 작성/수정 API는 `file_ids[]`를 받아 `file_map`에 다형 매핑 레코드 생성/교체 (`target_type=POST`, `target_id={post_id}`)
- 파일 검증 (게시판 `attach_ext` 설정에 따른 타입 허용. 번역기는 `image/*` 전용. 최대 크기·개수는 게시판 설정 준수)
- 이미지 미리보기 UI (업로드 즉시 프리뷰 표시 가능)
- 게시글 목록 조회 (페이지네이션, 게시판별)
- 게시글 상세 조회 (`file_map` 조인으로 첨부파일 포함)
- 게시글 수정 / 삭제 (파일 매핑 추가/해제는 `file_map` 조작)
- 댓글 작성 / 조회 (게시판 설정에 따라 사용 여부 결정)
- 게시판 UI (게시판 종류별 렌더링: LIST / IMAGE / QNA)

> **참고**: `file`, `file_map`의 상세 스키마와 다형 매핑 대상(POST, COMMENT 등) 규칙은 Domain / ERD 문서에서 확정한다.

---

### SFR-102: (통합됨 → SFR-106, Phase 1)

| 항목 | 내용 |
|------|------|
| **요구사항 고유번호** | ~~SFR-102~~ |
| **요구사항 명칭** | ~~OCR 텍스트 추출~~ |
| **상태** | **통합 · Phase 1 SFR-106으로 흡수** |
| **통합 대상** | SFR-106(고서 번역기, Phase 1). SFR-200(Phase 2 PDF 확장)에서도 동일 OCR 엔진 재사용. |

**통합 사유**:
원래 Phase 1에서 독립 기능으로 정의되었으나, OCR은 독립 트리거를 갖지 않고 번역 파이프라인의 한 단계로 동작한다. 파이프라인 자체가 Phase 1로 당겨지면서(SFR-106) OCR 엔진 추상화/구현은 SFR-106의 세부 범위로 흡수되었다. Phase 2의 PDF 다중 페이지 확장(SFR-200) 역시 동일 OCR 엔진을 재사용한다.

---

### SFR-103: (통합됨 → SFR-205)

| 항목 | 내용 |
|------|------|
| **요구사항 고유번호** | ~~SFR-103~~ |
| **요구사항 명칭** | ~~AI 자동 댓글 (파이프라인 결과)~~ |
| **상태** | **통합 · Phase 2로 이동** |
| **통합 대상** | [SFR-205 게시판 고서 파이프라인 자동 연동](#sfr-205-게시판-고서-파이프라인-자동-연동) |

**통합 사유**:
원래 "게시글 작성 시 이미지 첨부 → OCR+번역 파이프라인 **즉시 실행** → 댓글 등록"으로 정의되었으나, 이번 개정에서 트리거 방식이 **"게시판 설정 기반 자동 답변이 파이프라인을 활용"**하는 배치형 흐름으로 변경되었다. 즉시 실행 방식은 게시글 작성 UX 지연과 스케일링 부담이 크며, 자동 답변 스케줄러와 중복 로직이었다. 이 역할은 SFR-205(Phase 2, 게시판-파이프라인 연동 자동 답변)가 담당하고, Phase 1의 자동 답변은 텍스트 기반만 수행한다(SFR-104). 파이프라인 자체는 Phase 1 SFR-106(번역기)을 통해 존재한다.

---

### SFR-104: AI 자동 답변 (텍스트 기반)

| 항목 | 내용 |
|------|------|
| **요구사항 고유번호** | SFR-104 |
| **요구사항 명칭** | AI 자동 답변 (텍스트 기반) |
| **대상 Phase** | Phase 1 |
| **우선순위** | Must |

**정의**: 게시글 작성 후 해당 게시판 설정(`auto_reply_delay_min`, 기본 5분) 내에 **댓글이 하나도 달리지 않은 경우**, AI가 **게시글 본문 텍스트만을 기반으로** 답변을 생성하여 댓글로 등록한다. 댓글이 하나라도 존재하면(사용자 댓글이든 AI 댓글이든) 자동 답변 대상에서 제외된다. Phase 1에서는 이미지 첨부가 있어도 OCR/파이프라인을 수행하지 않는다.

**세부 내용**:
- 스케줄러 구현 (주기적 확인, 기본 1분 간격)
- 대상 게시글 조회 조건:
  - 게시판 `auto_reply_enabled=true`
  - 게시글 작성 후 `auto_reply_delay_min` 경과
  - 해당 게시글에 **댓글이 0건**
  - 자동 답변 상태(`auto_reply_status`)가 `pending`
- AI 답변 생성 (게시글 제목 + 본문 텍스트 전달)
- 자동 답변 댓글 등록 (author_type: ai_auto)
- `auto_reply_status`를 `completed`로 갱신

**Phase 2에서의 확장**: 게시판 설정 `pipeline_enabled=true`일 때 텍스트 기반 대신 파이프라인 기반 답변 수행 (SFR-205).

---

### SFR-105: 게시판 관리 (다중 게시판)

| 항목 | 내용 |
|------|------|
| **요구사항 고유번호** | SFR-105 |
| **요구사항 명칭** | 게시판 관리 (다중 게시판) |
| **대상 Phase** | Phase 1 |
| **우선순위** | Must |

**정의**: 서비스는 복수의 게시판을 DB 기반으로 운영한다. 각 게시판은 고유 코드, 표시명, 유형(`LIST`/`IMAGE`/`QNA`), 기능 플래그, AI 관련 설정을 보유한다. Phase 1에서는 게시판 목록 조회 및 초기 시드 게시판을 제공하며, 관리자 CRUD UI는 Phase 3에서 제공한다(SFR-300).

**세부 내용**:
- `boards` 테이블 도입 (다중 게시판 지원)
- 게시판 주요 속성:
  - 식별: `id`(ID-GEN 문자열), `board_code`(URL slug), `board_name`, `board_desc`
  - 표현: `board_type` (`LIST` 일반 목록형 / `IMAGE` 이미지 중심 / `QNA` 아코디언 질답형)
  - 기능: `notice_yn`, `comment_yn`, `attach_yn`, `attach_ext`, `attach_size`, `attach_count`, `list_count`
  - AI: `auto_reply_enabled`, `auto_reply_delay_min`(기본 5), `pipeline_enabled`(Phase 2부터 실제 동작)
  - 운영: `sort_order`, `use_yn`, `del_yn`/`deleted_at` (Soft Delete), `created_at`/`updated_at`
- 게시글(`posts`)은 `board_id` FK로 게시판에 귀속
- 게시판 목록 조회 API (클라이언트 네비게이션용)
- 초기 시드 게시판 제공 (예: 자유 토론, 고서 질문 등 — 실제 시드 구성은 구현 단계에서 확정)

**Phase 2에서의 확장**: `pipeline_enabled` 설정이 SFR-205의 판단 기준으로 활용된다.
**Phase 3에서의 확장**: 관리자 페이지에서 게시판 CRUD 및 설정 UI 제공(SFR-300).

---

### SFR-106: 고서 번역기 (이미지 1장, 파이프라인 정식 진입점)

| 항목 | 내용 |
|------|------|
| **요구사항 고유번호** | SFR-106 |
| **요구사항 명칭** | 고서 번역기 (이미지 1장) |
| **대상 Phase** | Phase 1 |
| **우선순위** | Must |

**정의**: 사용자가 고서 이미지 1장을 업로드하면 OCR + AI 번역 파이프라인을 실행하여 직역/의역 결과를 반환하는 **파이프라인의 정식 진입점**이다. 이 SFR이 OCR 엔진 추상화/구현과 번역 엔진 추상화/구현을 모두 담당하며, 이후 게시판 자동 답변(SFR-205, Phase 2)이 동일 파이프라인을 재사용한다. 번역기 접근은 로그인 필수(SFR-108).

**세부 내용**:
- 번역기 페이지 UI (`/translate`)
- 이미지 1장 업로드 (파일 업로드는 SFR-101의 `file` + `file_map` 구조 재사용)
- **OCR 엔진 인터페이스 및 구현**
  - PaddleOCR (1순위)
  - Google Vision API (2순위, 인식률 부족 시 전환)
  - OCR 결과 저장: 추출 텍스트, 사용 엔진, 신뢰도
- **AI 번역 엔진 인터페이스 및 구현**
  - Gemini Flash (1순위, 무료)
  - Claude Haiku (2순위, 품질 부족 시)
  - 직역/의역 분리 생성
- 파이프라인 오케스트레이션: OCR → 번역 → 결과 저장
- 파이프라인 실행 상태 관리 (진행중/완료/실패, `pipeline_runs` 로깅)
- 결과 표시: 직역/의역 나란히 비교
- Book/Page 구조로 저장
  - `book_type='QUICK'`으로 Book 1건 + `book_pages` 1건 자동 생성
  - 자동 제목: `"빠른 번역 YYYY-MM-DD HH:mm"` (사용자가 수정 가능)

**Phase 2에서의 확장**: PDF 다중 페이지 지원 (SFR-200), 사용자 등록 Book (`USER_CREATED`), 요약/키워드/빈도수(SFR-202), 번역 수정(SFR-201), 공유(SFR-203).

---

### SFR-107: 라이브러리 (내 번역 이력, 단순 리스트)

| 항목 | 내용 |
|------|------|
| **요구사항 고유번호** | SFR-107 |
| **요구사항 명칭** | 라이브러리 (내 번역 이력) |
| **대상 Phase** | Phase 1 |
| **우선순위** | Must |

**정의**: 로그인 사용자가 본인이 만든 번역 Book 목록을 조회할 수 있는 라이브러리 페이지. Phase 1에서는 단순 리스트 형태로 제공하며, Phase 2에서 탭 구조 및 즐겨찾기로 확장된다(SFR-206).

**세부 내용**:
- 라이브러리 페이지 UI (`/library`)
- 본인 소유 `books` 조회 (`books.owner_user_id = current_user.id`)
- 단순 리스트 (탭 구분 없음, Phase 1엔 모두 `book_type='QUICK'`)
- 정렬: 최신순 기본, 제목순 옵션
- Book 제목 수정 가능 (`PATCH /books/:id` — 본인 소유만)
- Book 삭제 가능 (Soft Delete)
- 보관 정책: 영구 (사용자 수동 삭제만)
- **비로그인 접근 시**: 로그인 안내 화면

**Phase 2에서의 확장**: SFR-206에서 탭 구조("내 책" / "빠른 번역") + 즐겨찾기(`books.is_favorite`) + 제목 검색 도입.

---

### SFR-108: 사용자 인증 (OAuth: Google + Kakao)

| 항목 | 내용 |
|------|------|
| **요구사항 고유번호** | SFR-108 |
| **요구사항 명칭** | 사용자 인증 (OAuth) |
| **대상 Phase** | Phase 1 |
| **우선순위** | Must |

**정의**: Google과 Kakao OAuth 2.0을 지원하는 로그인 시스템을 구현한다. LOCAL 로그인은 지원하지 않으며, 개인정보 최소 수집 원칙을 따른다. 게시글/댓글 작성, 번역기 사용, 라이브러리 접근은 로그인 필수이며, 비로그인 사용자는 게시글 읽기만 가능하다.

**세부 내용**:
- **OAuth Provider**: Google, Kakao 둘 다 지원
- **스키마**:
  - `users` 테이블 (내부 PK `USER_00000001` 형식)
  - `user_oauth` 테이블 (users와 1:N 관계, 한 사용자가 Google+Kakao 모두 연결 가능)
  - `UNIQUE (user_oauth.provider, user_oauth.provider_user_id)`
- **개인정보 수집 범위**: `email`, `name`, `profile_image_url`만 저장. 전화번호/login_id 미수집
- **권한 체계** (`users.user_level`):
  - `GUEST` = 0 (비로그인)
  - `USER` = 10 (일반 사용자)
  - `ADMIN` = 70 (앱 관리자, Phase 3 활성화)
  - `SYSTEM_ADMIN` = 100 (시스템 관리자, Phase 3 활성화)
- **비로그인 접근 제약 (Phase 1부터 적용)**:
  - 게시글 읽기: 허용
  - 게시글/댓글 작성: 차단 (로그인 필요)
  - 번역기 사용: 차단 (로그인 필요)
  - 라이브러리 접근: 차단 (로그인 필요)
- **권한 체크 구현**: 데코레이터 방식 (`@require_level(UserRole.USER)` 등). Phase 1에는 `USER` 레벨까지만 사용, `ADMIN/SYSTEM_ADMIN` 데코레이터는 Phase 3에서 활성화.
- **로그인 이벤트 기록**: OAuth 로그인/실패 시 `login_log` 테이블에 INSERT (조회 UI는 Phase 3 SFR-303).
- **세션/토큰**: JWT 기반, 세부 설정(만료 시간 등)은 구현 단계에서 확정.
- **최초 관리자 부트스트랩** (Phase 3 활성화): 환경변수 `INITIAL_ADMIN_EMAILS`에 지정된 이메일로 OAuth 로그인 시 자동으로 `user_level=100` 승격 (1회).

---

## 6. Phase 2 요구사항 상세

### SFR-200: 고서 번역 파이프라인 (번역기)

| 항목 | 내용 |
|------|------|
| **요구사항 고유번호** | SFR-200 |
| **요구사항 명칭** | 고서 번역 파이프라인 (번역기) |
| **대상 Phase** | Phase 2 |
| **우선순위** | Should |

**정의**: SFR-106(Phase 1, 이미지 1장)을 확장하여 **PDF 다중 페이지 번역**을 지원한다. 사용자가 PDF를 업로드하면 서버에서 페이지별 이미지로 분할한 뒤, 각 페이지에 대해 SFR-106의 파이프라인을 동일하게 실행한다. 또한 사용자가 직접 "책"을 등록하고 여러 이미지/PDF를 순차적으로 추가할 수 있는 `book_type='USER_CREATED'` 모드를 도입한다.

**세부 내용**:
- PDF 업로드 지원
  - 최대 100페이지 / 50MB
  - 서버에서 페이지별 이미지 변환 (분할 라이브러리 및 해상도 기준은 구현 단계에서 확정)
  - 각 페이지를 `book_pages`에 개별 레코드로 저장
- 사용자 등록 Book (`book_type='USER_CREATED'`)
  - 사용자가 책 먼저 등록 (제목, 설명 등)
  - 이후 해당 Book에 이미지/PDF를 순차적으로 추가 가능
  - Book 단위로 페이지 순서 관리
- 페이지별 파이프라인 실행 (백그라운드)
  - 페이지별 진행률 UI
  - 부분 실패 처리 정책(전체 실패 vs 부분 진행)은 구현 단계에서 확정
- 엔진 폴백 전략(Gemini 실패 → Claude)은 구현 단계에서 확정

---

### SFR-201: 번역 결과 수정 (본인 소유만)

| 항목 | 내용 |
|------|------|
| **요구사항 고유번호** | SFR-201 |
| **요구사항 명칭** | 번역 결과 수정 (본인 소유만) |
| **대상 Phase** | Phase 2 |
| **우선순위** | Should |

**정의**: AI가 생성한 직역/의역 번역 결과를 **본인 소유 Book에 한해** 사용자가 직접 수정할 수 있는 기능을 제공한다. 수정 전 원본은 `page_revisions` 테이블에 append-only로 보존되어 롤백이 가능하다. 타인 번역에 대한 수정 제안(suggestion) 기능은 Phase 3에서 도입한다(SFR-305).

**세부 내용**:
- 직역/의역 텍스트 인라인 편집 UI (`book_pages.literal_text`, `book_pages.interpretive_text`)
- **권한 규칙**: `book.owner_user_id == current_user.id`인 경우에만 편집 가능 (아니면 403)
- 수정 이력:
  - `page_revisions` 테이블에 수정 전 버전 append-only 저장
  - 컬럼: `page_id`, `literal_text`, `interpretive_text`, `edited_by`, `created_at`
  - 복구(rollback) 기능: 사용자가 이전 버전 선택 시 현재를 revision으로 저장하고 선택 버전을 현재값으로 반영
- 수정 여부 표시 UI (원본 AI 번역과 차이 시각화, 선택)

---

### SFR-202: 핵심 요약 / 키워드 / 빈도수

| 항목 | 내용 |
|------|------|
| **요구사항 고유번호** | SFR-202 |
| **요구사항 명칭** | 핵심 요약 / 키워드 / 빈도수 |
| **대상 Phase** | Phase 2 |
| **우선순위** | Should |

**정의**: Book 단위로 핵심 요약, 키워드 추출, 단어 빈도수를 제공한다. 번역 파이프라인 완료 직후 자동 실행하여 결과를 DB에 저장하며, 재계산 부담을 줄인다.

**세부 내용**:
- **실행 시점**: 번역 파이프라인 완료 직후 자동 실행 (결과 저장)
- **요약**: Book 단위 (모든 페이지의 번역 결과를 종합), 2~5줄 핵심 요약
  - 구현: LLM (Gemini Flash / Claude Haiku) 호출
- **키워드 추출**: `kiwipiepy` 기반 형태소 분석 (명사/고유명사 추출)
  - **LLM 미호출** (비용/지연 절감)
- **단어 빈도수**: `kiwipiepy` + `Counter` 로 상위 N개 산출
- 요약/키워드/빈도수 표시 UI (Book 상세 페이지)
- 페이지 단위 요약은 본 SFR의 범위 외 (필요 시 추후 확장)

---

### SFR-203: 결과 저장 / 공유

| 항목 | 내용 |
|------|------|
| **요구사항 고유번호** | SFR-203 |
| **요구사항 명칭** | 결과 저장 / 공유 |
| **대상 Phase** | Phase 2 |
| **우선순위** | Should |

**정의**: 번역 결과를 영구 저장하고, 소유자가 명시적으로 공유를 활성화했을 때에 한해 고유 링크를 통해 외부에 열람을 허용한다. 공유 링크는 열람 전용이며 편집은 불가하다.

**세부 내용**:
- 번역 결과 영구 저장 (`books`, `book_pages`에 자동 저장, SFR-106/SFR-200 범위)
- **공유 링크 생성**:
  - `books.share_token VARCHAR(100) NULLABLE` (UUID 기반)
  - owner가 "공유" 버튼을 눌러 활성화하면 `share_token` 채움 (NULL이면 공유 OFF)
  - URL: `/s/:share_token`
- **기본값**: 공유 OFF (owner의 명시적 활성화 필요)
- **공유 링크 접근**:
  - 비로그인 접근 허용 (열람만)
  - 편집/수정/삭제는 불가 (owner 외에는 403)
- **비공개 전환**: owner가 공유 OFF로 바꾸면 `share_token` NULL로 되돌려 링크 무효화
- **URL 형태**: `book.id` 기반 URL(`/books/:id`)은 owner 전용 라이브러리 접근 경로, 공유는 별도 토큰 URL로만

---

### SFR-204: (Phase 3으로 이동 → SFR-304)

| 항목 | 내용 |
|------|------|
| **요구사항 고유번호** | ~~SFR-204~~ |
| **요구사항 명칭** | ~~참고자료 추천~~ |
| **상태** | **이동 · Phase 3으로 재배치** |
| **신규 번호** | SFR-304 (Phase 3) |

**이동 사유**:
참고자료 추천은 LLM 환각(hallucination) 위험, 학술 검색 API 연동 복잡도, 한국 고서 도메인 특화 데이터 부재 등 구현 난이도가 높다. Phase 2 MVP 스코프로는 부담이 크며, 구현 방식(LLM 직접 추천 / 외부 검색 API / 사전 DB / 키워드 자동 주입 검색 링크 등)을 Phase 3 착수 시 별도 회의로 확정한다.

---

### SFR-205: 게시판 고서 파이프라인 자동 연동

| 항목 | 내용 |
|------|------|
| **요구사항 고유번호** | SFR-205 |
| **요구사항 명칭** | 게시판 고서 파이프라인 자동 연동 |
| **대상 Phase** | Phase 2 |
| **우선순위** | Should |

**정의**: 게시판 설정 `pipeline_enabled=true`인 게시판에 대해, AI 자동 답변(SFR-104 확장)이 SFR-200의 고서 번역 파이프라인을 호출하여 OCR + 직역/의역 + 요약 + 키워드가 포함된 풍부한 답변을 댓글로 등록한다. **SFR-103(Phase 1 제안이었던 즉시 실행 자동 댓글)을 흡수**한다.

**세부 내용**:
- 기존 SFR-104(텍스트 기반 자동 답변)의 로직을 확장:
  - 대상 게시판 조회 시 `auto_reply_enabled=true AND pipeline_enabled=true` 필터 추가
  - 파이프라인 경로: 이미지 첨부 글 → OCR → 번역 → 요약/키워드 → 댓글 등록
  - 텍스트 전용 게시판(`pipeline_enabled=false`)은 기존 SFR-104 경로 유지
- 자동 답변 댓글의 `author_type`:
  - 텍스트 기반: `ai_auto`
  - 파이프라인 기반: `ai_pipeline`
- 게시판별 설정(`pipeline_enabled`)은 `boards` 테이블 컬럼으로 관리 (SFR-105)
- Phase 2에서는 설정 변경이 DB 직접 수정 또는 시드 기반, Phase 3 관리자 UI에서 편집(SFR-300)

---

### SFR-206: 라이브러리 확장 (탭 구조 + 즐겨찾기 + 제목 검색)

| 항목 | 내용 |
|------|------|
| **요구사항 고유번호** | SFR-206 |
| **요구사항 명칭** | 라이브러리 확장 |
| **대상 Phase** | Phase 2 |
| **우선순위** | Should |

**정의**: SFR-107(Phase 1 단순 리스트)을 확장하여 Book 종류별 탭 구조, 즐겨찾기, 제목 검색 기능을 제공한다.

**세부 내용**:
- **탭 구조**:
  - "내 책" 탭: `book_type='USER_CREATED'`
  - "빠른 번역" 탭: `book_type='QUICK'`
- **즐겨찾기**:
  - `books.is_favorite BOOLEAN` 컬럼 (Phase 1 스키마에 선반영되어 있음)
  - 라이브러리에서 필터 제공 ("즐겨찾기만 보기")
  - 본인 소유 Book만 대상 (별도 매핑 테이블 불필요)
- **제목 검색**:
  - 제목(`books.title`) 대상 LIKE 검색
  - 전문 검색(OCR/번역 텍스트)은 범위 외 (Phase 3 이후 검토)
- 정렬: 최신순/제목순/페이지수순

---

## 7. Phase 3 요구사항 상세

### SFR-300: 관리자 페이지 (1차 표준)

| 항목 | 내용 |
|------|------|
| **요구사항 고유번호** | SFR-300 |
| **요구사항 명칭** | 관리자 페이지 (1차 표준) |
| **대상 Phase** | Phase 3 |
| **우선순위** | Should |

**정의**: 관리자 전용 웹 앱(`apps/admin`)을 통해 시스템의 핵심 관리 작업을 수행한다. 1차 표준 범위로 게시판·게시글·댓글·사용자 관리와 악성댓글 검수를 포함하며, 시간 여유 시 풀스펙(시스템 로그 뷰어, 파이프라인 재실행, 엔진 전환)까지 확장한다.

**세부 내용 (1차 표준)**:
- 관리자 전용 웹 앱 (`apps/admin`) 신설 (별도 빌드/배포)
- **게시판 관리 (CRUD)**: 게시판 생성/수정/삭제, `board_type`(LIST/IMAGE/QNA) 선택, 기능 플래그 편집
- **게시판별 설정 편집**: `pipeline_enabled`, `auto_reply_enabled`, `auto_reply_delay_min`, `attach_*`
- **게시글 관리**: 강제 삭제/복구, 검색
- **댓글 관리**: 삭제, 필터링 해제(SFR-301)
- **사용자 관리**: 차단/해제, 권한 승격(USER↔ADMIN), 탈퇴 복구
- **OAuth 세션 공유**: `apps/client`와 동일 세션 사용 (별도 로그인 없이 도메인 기반 세션 공유)
- **기본 통계 대시보드**: 일일 게시글/댓글/번역 수, 로그인 사용자 수

**세부 내용 (2차 풀스펙, 시간 여유 시)**:
- 시스템 로그 뷰어 (SYSTEM_ADMIN 전용)
- 파이프라인 재실행 UI
- OCR/번역 엔진 전환 UI (Settings 편집)

---

### SFR-301: 악성댓글 AI 필터링

| 항목 | 내용 |
|------|------|
| **요구사항 고유번호** | SFR-301 |
| **요구사항 명칭** | 악성댓글 AI 필터링 |
| **대상 Phase** | Phase 3 |
| **우선순위** | Could |

**정의**: AI(Gemini/Claude)를 활용하여 댓글을 주기적으로 검수하고 악성으로 판별된 댓글은 UI에서 안내 문구로 대체한다. 사용자는 "내용 보기"로 원본을 확인할 수 있고, 관리자는 필터 해제가 가능하다.

**세부 내용**:
- **판별 방식**: LLM (Gemini Flash 1순위, Claude Haiku 2순위)에 분류 프롬프트 전달
- **실행 방식**: 주기적 배치 (스케줄러)
- **대상**: `comments.is_filtered=false AND filtered_at IS NULL`인 신규 댓글 (중복 검수 방지)
- **필터링된 댓글 UI**:
  - 기본 표시: "AI에 의해 필터링된 댓글입니다"
  - 사용자가 "내용 보기" 클릭 시 원본 열람 가능 (접힘/펼침)
- **관리자 기능**: 필터 해제 (`is_filtered=false`, `filter_reviewed_by`에 관리자 ID 기록)
- **스키마 확장** (`comments`):
  - `is_filtered BOOLEAN DEFAULT false`
  - `filter_reason VARCHAR(200) NULLABLE` (AI 판별 근거)
  - `filtered_at TIMESTAMPTZ NULLABLE`
  - `filter_reviewed_by VARCHAR(20) NULLABLE` (FK users.id, 필터 해제한 관리자)
  - 위 컬럼은 Phase 1 스키마에 선반영되어 default 값으로 무해하게 존재 (이는 SFR-101 참조)

---

### SFR-302: 사용자 권한 관리 (ADMIN/SYSTEM_ADMIN 데코레이터 활성화)

| 항목 | 내용 |
|------|------|
| **요구사항 고유번호** | SFR-302 |
| **요구사항 명칭** | 사용자 권한 관리 |
| **대상 Phase** | Phase 3 |
| **우선순위** | Should |

**정의**: Phase 1(SFR-108)에서 스키마·`user_level` 컬럼·권한 Enum은 도입되어 있으나, ADMIN/SYSTEM_ADMIN 레벨의 실제 권한 체크는 Phase 3 관리자 페이지(SFR-300) 등장에 맞추어 활성화된다. 본 SFR은 해당 데코레이터 활성화 및 권한 승격 플로우를 정의한다.

**세부 내용**:
- **데코레이터 활성화**: `@require_level(UserRole.ADMIN)`, `@require_level(UserRole.SYSTEM_ADMIN)` 을 관리자 API에 적용
- **최초 관리자 부트스트랩**: 환경변수 `INITIAL_ADMIN_EMAILS` 목록에 해당하는 이메일로 OAuth 로그인 시 자동 `user_level=100` (SYSTEM_ADMIN) 승격 (1회만)
- **관리자 간 권한 관리**:
  - 기존 ADMIN/SYSTEM_ADMIN이 관리자 페이지(SFR-300)에서 다른 사용자 레벨 변경
  - 권한 변경 이력은 `admin_audit_log`에 기록 (SFR-303)
- **비상 복구**: DB 직접 `UPDATE users SET user_level=100 WHERE ...` (SYSTEM_ADMIN 대상)

---

### SFR-303: 관리자 로그 뷰어 (login_log / admin_audit_log)

| 항목 | 내용 |
|------|------|
| **요구사항 고유번호** | SFR-303 |
| **요구사항 명칭** | 관리자 로그 뷰어 |
| **대상 Phase** | Phase 3 |
| **우선순위** | Should |

**정의**: 관리자 페이지에서 `login_log`(로그인 이벤트)와 `admin_audit_log`(관리자 작업 이력)를 조회/검색할 수 있는 UI를 제공한다. 로그 테이블 스키마와 INSERT 동작은 아래와 같이 단계적으로 도입된다.

**세부 내용**:
- **`login_log`**: 
  - 스키마 Phase 1 선반영
  - Phase 1부터 OAuth 로그인 시 INSERT (성공/실패 모두)
  - 컬럼: `user_id`, `provider`, `provider_email`, `ip_address`, `user_agent`, `result`, `fail_reason`, `created_at`
  - Phase 3에서 관리자 페이지 조회 UI 제공
- **`admin_audit_log`**:
  - 스키마 Phase 1 선반영
  - Phase 3에서 INSERT 시작 (관리자 기능이 Phase 3에 등장)
  - 컬럼: `admin_user_id`, `action`, `target_type`, `target_id`, `payload`(JSONB), `ip_address`, `created_at`
  - Phase 3에서 관리자 페이지 조회 UI 제공
- **조회 기능**: 날짜/사용자/액션 필터, 페이지네이션

---

### SFR-304: 참고자료 추천 (Phase 2에서 이동)

| 항목 | 내용 |
|------|------|
| **요구사항 고유번호** | SFR-304 |
| **요구사항 명칭** | 참고자료 추천 |
| **대상 Phase** | Phase 3 |
| **우선순위** | Could |

**정의**: 번역된 고서 내용과 관련된 참고자료(논문, 문헌 등)를 추천한다. 구현 난이도가 높아 Phase 3 착수 시 별도 회의를 통해 구현 방식을 확정한다.

**구현 방식 후보 (Phase 3 착수 시 확정)**:
- (a) LLM 직접 추천 (환각 위험 주의)
- (b) 외부 학술 검색 API 연동 (KCI, DBpia, CrossRef 등)
- (c) 사전 수작업 DB (품질 보장, 확장성 낮음)
- (d) 하이브리드 (LLM으로 키워드 추출 → 외부 API로 실제 자료 조회)
- (e) 단순 검색 링크만 제공 (키워드 자동 주입하여 Google Scholar 등 검색 URL 생성, 사용자가 직접 탐색)

**세부 내용**:
- 번역 결과 상세 페이지에 참고자료 섹션 추가
- 논문/문헌 링크 제공 (파일 호스팅은 범위 외)

---

### SFR-305: 타인 번역 제안 (suggestion)

| 항목 | 내용 |
|------|------|
| **요구사항 고유번호** | SFR-305 |
| **요구사항 명칭** | 타인 번역 제안 |
| **대상 Phase** | Phase 3 |
| **우선순위** | Could |

**정의**: SFR-201(본인 번역 수정)을 확장하여, 타 사용자가 공유된 Book의 번역에 대해 수정 제안(suggestion)을 등록할 수 있는 기능을 제공한다. 원본은 보존되고, owner가 승인해야 반영된다.

**세부 내용**:
- 제안 등록: 로그인 사용자가 공유 Book의 페이지별 제안 등록 (직역/의역 각각)
- 제안 승인 플로우: owner가 제안 목록을 보고 수락/거부
- 수락 시 기존 번역은 `page_revisions`로 이력화, 제안 내용이 현재값으로 반영
- 알림/신뢰점수 등 부가 설계는 Phase 3 착수 시 회의로 확정

---

## 8. 비기능 요구사항

### 8.1 성능

| 항목 | 기준 |
|------|------|
| OCR + 번역 파이프라인 | 30초 이내 (A4 1페이지 기준) |
| 게시판 API 응답 | 500ms 이내 |
| 이미지 업로드 | 최대 10MB |

### 8.2 보안

| 항목 | 대응 |
|------|------|
| 파일 업로드 | 이미지 타입만 허용, 최대 10MB 제한 |
| XSS | 출력 이스케이핑, Content Security Policy |
| SQL Injection | ORM 사용, 파라미터 바인딩 |
| CORS | 허용 오리진 명시적 설정 |

### 8.3 가용성 및 배포

- Docker Compose 기반으로 로컬 및 클라우드 환경 모두 지원
- 각 앱(client, server, admin)은 독립적으로 빌드/배포 가능

### 8.4 호환성

- 최신 Chrome, Edge, Firefox 지원
- PC 환경 우선 (모바일은 웹 반응형으로 대응)

---

## 9. 제약 조건

- OCR 엔진(PaddleOCR)의 고문서 인식률이 현대 문서 대비 낮을 수 있음 (인식률 부족 시 Google Vision API로 전환 가능)
- AI 번역 품질은 모델(Gemini Flash / Claude Haiku)의 한문 이해도에 의존
- 무료 API(Gemini Flash) 사용 시 호출 제한(Rate Limit)이 존재할 수 있음
- **인증은 Phase 1부터 OAuth(Google + Kakao)로 적용**. 비로그인 사용자는 게시글 읽기와 공유 링크 열람만 가능 (글쓰기/번역기/라이브러리는 로그인 필수)
- 개인정보 최소 수집 원칙 (email, name, profile_image_url만). 전화번호 등은 수집하지 않음
- 시연/운영 시 외부 API 레이트 리밋 위험이 큰 경우, 자체 호스팅 vLLM 엔진을 백업 옵션으로 검토 가능 (§ Architecture ADR 참조)

---

## 10. 용어 정의

| 용어 | 정의 |
|------|------|
| **고서** | 한문 또는 한글로 작성된 역사적 문서 (고문서, 고전 문헌) |
| **OCR** | Optical Character Recognition, 이미지에서 텍스트를 인식/추출하는 기술 |
| **직역** | 원문의 글자를 그대로 한글로 대응하여 번역한 결과 |
| **의역** | 원문의 의미를 현대 한국어로 자연스럽게 풀어 번역한 결과 |
| **파이프라인** | OCR → 번역 → 후처리까지의 자동화된 처리 흐름 |
| **AI 자동 답변** | 설정된 대기 시간(`board.auto_reply_delay_min`, 기본 5분) 경과 후에도 댓글이 0건인 게시글에 AI가 자동으로 등록하는 댓글 |
| **필터링 댓글** | AI가 부적절하다고 판별하여 "AI에 의해 필터링된 댓글입니다"로 대체 표시되는 댓글 (사용자가 "내용 보기"로 원본 확인 가능) |
| **Book** | 번역 요청 단위. `QUICK`(이미지 1장 자동 생성) 또는 `USER_CREATED`(사용자가 책 먼저 등록 후 이미지/PDF 추가)로 구분 |
| **BookPage** | Book 내부의 페이지별 번역 결과 단위 |
| **라이브러리** | 로그인 사용자가 본인이 만든 Book 목록을 조회하는 페이지 |
| **파이프라인 진입점** | 번역기(SFR-106/SFR-200)를 지칭. 게시판 자동 답변(SFR-205)은 동일 파이프라인을 재사용 |

---

## 11. 변경 이력

| 날짜 | 버전 | 변경 내용 | 작성자 |
|------|------|----------|--------|
| 2026-04-02 | v1.0 | 초안 작성 | - |
| 2026-04-13 | v1.1 | 다중 게시판 도입(SFR-105), SFR-102/103 통합, Phase 1 자동답변 텍스트 기반으로 명확화 등 (상세는 Architecture v1.2 참조) | - |
| 2026-04-13 | v1.2 | Phase 로드맵 재구성(OCR 파이프라인 Phase 1로 당김, OAuth Phase 1 당김). 신규 SFR: SFR-106(번역기 이미지 1장), SFR-107(라이브러리), SFR-108(OAuth), SFR-206(라이브러리 확장), SFR-303(로그 뷰어), SFR-305(타인 번역 제안). SFR-204→SFR-304(Phase 3 이동). SFR-200 재정의(PDF 확장에 집중). SFR-201(본인만), SFR-202(kiwipiepy 로컬), SFR-203(share_token) 세부 반영. SFR-300(관리자 1차 표준) 재정의. SFR-301(악성댓글 UX). SFR-302(권한 데코레이터 활성화) 재정의. | - |
| 2026-04-13 | v1.2.1 | 리뷰 보정: SFR-103 tombstone 통합 사유 재작성(파이프라인 부재 → 트리거 방식 변경). Phase 2+ Must → Should 우선순위 조정(SFR-200/205/300/302) | - |
