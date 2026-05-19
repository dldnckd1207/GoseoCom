---
status: active
created: 2026-04-15
updated: 2026-04-15
parent: "[[02_SRS]]"
---

# SRS Phase 1 — 요구사항 명세

| 항목 | 내용 |
|------|------|
| **제품명** | Haedok AI (解讀 AI) |
| **버전** | v1.0 |
| **작성일** | 2026-04-15 |
| **참조 문서** | [02_SRS.md](../02_SRS.md), [03_Architecture.md](../03_Architecture.md), [04_Domain.md](../04_Domain.md), [05_ERD.md](../05_ERD.md) |

---

## 1. Phase 1 목표

| 항목 | 내용 |
|------|------|
| **목표** | 핵심 기능(게시판 + 번역기) MVP 배포 |
| **범위** | 백엔드(FastAPI) + 프론트엔드(Remix) |
| **인증** | OAuth 전용 (Google + Kakao), LOCAL 로그인 없음 |
| **OCR** | Google Vision API (GPU 미확보, PaddleOCR은 Phase 2) |
| **번역** | Gemini Flash (1순위, 무료) / Claude Haiku (2순위) |
| **파일 저장** | 로컬 스토리지 (S3 전환은 Phase 2) |
| **관리자 UI** | Phase 3 (디렉토리 구조만 Phase 1 준비) |

---

## 2. SFR 목록

| SFR | 기능명 | 우선순위 | 상태 | 상세 문서 |
|-----|--------|---------|------|----------|
| SFR-100 | 프로젝트 기반 구축 | Must | ✅ 완료 | [SFR-100](../../sdd/srs_p1/SFR-100_BE_기반구축.md) |
| SFR-108 | 사용자 인증 (OAuth) | Must | ✅ 완료 | [SFR-108](../../sdd/srs_p1/SFR-108_BE_OAuth인증.md) |
| SFR-105 | 게시판 관리 (다중 게시판) | Must | ✅ 완료 | [SFR-105](../../sdd/srs_p1/SFR-105_BE_다중게시판.md) |
| SFR-101 | 게시판 CRUD | Must | ✅ 완료 | [SFR-101](../../sdd/srs_p1/SFR-101_BE_게시판CRUD.md) |
| SFR-106 | 고서 번역기 (이미지 1장) | Must | 🔲 대기 | [SFR-106](../../sdd/srs_p1/SFR-106_BE_고서번역기.md) |
| SFR-107 | 라이브러리 (번역 이력) | Must | 🔲 대기 | [SFR-107](../../sdd/srs_p1/SFR-107_BE_라이브러리.md) |
| SFR-104 | AI 자동 답변 (텍스트 기반) | Must | 🔲 대기 | [SFR-104](../../sdd/srs_p1/SFR-104_BE_AI자동답변.md) |

> 구현 권장 순서: SFR-108 → SFR-105 → SFR-101 → SFR-106 → SFR-107 → SFR-104

---

## 3. 공통 규칙

### 3.1 API 컨벤션

| 항목 | 규칙 |
|------|------|
| Base URL | `/api/v1/` |
| HTTP Method | `POST`(생성) / `PUT`(수정) / `DELETE`(삭제) / `GET`(조회), `PATCH` 미사용 |
| 인증 방식 | JWT + httpOnly 쿠키 (Stateless, XSS 방어) |
| 쿠키 설정 | `httpOnly=true`, `SameSite=Lax`, `Secure=true`(운영) |
| 에러 응답 | `{ "code": "ERROR_CODE", "message": "설명" }` |
| 페이지네이션 | `?page=1&size=20` (기본 size=20) |

### 3.2 인증 / 권한

| user_level | 역할 | Phase 1 활성 |
|-----------|------|-------------|
| 0 | GUEST (비로그인) | ✅ |
| 10 | USER (일반 사용자) | ✅ |
| 70 | ADMIN | ✅ (Admin UI는 Phase 3) |
| 100 | SYSTEM_ADMIN | ✅ (Admin UI는 Phase 3) |

> ADMIN/SYSTEM_ADMIN **역할(권한 레벨)**은 Phase 1부터 활성. API 레벨 권한 체크(`require_level`)에 사용.
> **Admin UI(관리자 페이지)**는 Phase 3에서 구현. Phase 1은 Swagger로 관리.

- 권한 체크: `require_level(UserRole.X)` Dependency 사용
- 비로그인 허용: 게시글 읽기만 (게시판 설정 `guest_read_yn` 따름)
- 비로그인 차단: 게시글/댓글 작성, 번역기, 라이브러리

**JWT 토큰 정책:**

| 항목 | 값 |
|------|-----|
| Access Token | httpOnly 쿠키, 만료 1시간 |
| Refresh Token | httpOnly 쿠키, 만료 30일, DB 저장 (`com_tn_user_token`) |
| 쿠키 설정 | `httpOnly=true`, `SameSite=Lax`, `Secure=true`(운영) |
| Rotation | Refresh Token 사용 시 새 토큰 발급 + 이전 토큰 무효화 |
| 탈취 감지 | 무효화된 토큰 재사용 시 → 해당 유저 전체 세션 무효화 |

### 3.3 ID 채번 전략

| 테이블 | PREFIX | 예시 |
|--------|--------|------|
| `com_tn_user` | `USR_` | `USR_00000001` |
| `com_tn_user_oauth` | `OAUTH_` | `OAUTH_00000001` |
| `com_tn_file` | `FILE_` | `FILE_00000001` |
| `com_tn_file_map` | `FMAP_` | `FMAP_00000001` |
| `cms_tn_board` | `BRD_` | `BRD_00000001` |
| `cms_tn_board_category` | `BCAT_` | `BCAT_00000001` |
| `cms_tn_post` | `POST_` | `POST_00000001` |
| `cms_tn_comment` | `CMT_` | `CMT_00000001` |
| `ai_tn_book` | `BOOK_` | `BOOK_00000001` |
| `ai_tn_book_page` | `BPAGE_` | `BPAGE_00000001` |
| `com_tn_user_token` | `UTKN_` | `UTKN_00000001` |
| 로그/이력 (History 테이블) | — | BIGSERIAL (`1`, `2`, `3`) |
| AI 에이전트 (고정값) | `USR_` | `USR_00000000` |

- 형식: `{PREFIX}{8자리 숫자}` (예: `USR_00000001`)
- 최대 99,999,999건

### 3.4 파일 업로드 / 서빙

| 구분 | 엔드포인트 | 담당 모듈 | 설명 |
|------|-----------|---------|------|
| 게시판 파일 업로드 | `POST /api/v1/boards/{board_code}/uploads` | `board/` | 게시판 정책 검증 후 파일 저장 |
| 일반 파일 업로드 | `POST /api/v1/uploads` | `core/files/` | 번역기 등 board context 없는 업로드 |
| 파일 서빙 | `GET /files/{uuid}` | `core/files/` | target_type 기반 접근 제어 |
| 강제 다운로드 | `GET /files/{uuid}?download=true` | `core/files/` | `Content-Disposition: attachment` 헤더 추가 |

**모듈 역할 분리:**
- `board/` — 게시판 정책 검증 (`attach_size`, `attach_ext`, `attach_count`) 후 `core/files/service` 호출
- `core/files/` — 파일 저장/조회 인프라 (공통 서비스, 모든 도메인에서 재사용)

**파일 접근 제어 (target_type 기준):**

| target_type | 접근 권한 |
|------------|---------|
| `POST` / `COMMENT` | 해당 게시판 설정 준수 (비로그인 허용 게시판이면 파일도 허용) |
| `BOOK` | 로그인 필수 + 본인 소유 확인 |

- 연결: `file_map` 테이블 (`target_type` / `target_id` / `file_group`)
- Phase 1 저장: 로컬 스토리지, 년/월 기준 디렉토리 분산
- 서빙 흐름: `Browser → nginx /files/* → FastAPI → 파일 응답`
- nginx는 `/files/`를 FastAPI로 reverse proxy (직접 파일 서빙 아님)

**파일 저장 구조:**

| 항목 | 값 | 비고 |
|------|-----|------|
| 디스크 경로 | `storage/files/{YYYY}/{MM}/{uuid}.ext` | 원본 파일명 미사용 |
| url_path (DB) | `/files/{uuid}` | 클라이언트 노출, 경로 정보 없음 |
| local_path (DB) | `storage/files/{YYYY}/{MM}/{uuid}.ext` | 서버만 참조, 노출 안 함 |

- 업로드 시 원본 파일명은 `com_tn_file.original_name` 컬럼에만 보존
- 디스크에는 UUID 기반 파일명으로 저장하여 실제 경로 은닉

### 3.5 소프트 삭제 (Soft Delete)

테이블 성격에 따라 삭제 방식이 다릅니다.

| 구분 | 해당 테이블 | 삭제 방식 |
|------|------------|----------|
| **엔티티** | `user`, `file`, `file_map`, `board`, `post`, `comment`, `book`, `book_page` | Soft Delete — `del_yn`, `deleted_at`, `deleted_by` 컬럼 보유 |
| **연결 관계** | `user_oauth` | Soft Delete → 탈퇴 3개월 후 Hard Delete (스케줄러) |
| **이력/로그** | `login_log`, `post_history`, `pipeline_run`, `admin_audit_log` | Append-only — 삭제 없음 |

- 엔티티 조회 시 `del_yn = false` 조건 기본 적용

**file_map 첨부/탈부착 패턴:**
- 첨부 시: `(file_id, target_type, target_id)` 기준 기존 row 있으면 `del_yn=false` UPDATE, 없으면 INSERT
- 탈부착 시: `del_yn=true` Soft Delete

### 3.6 AI 에이전트

- ID: `USR_00000000` (고정값, "해독이" 가칭)
- 판별: `is_ai_gen` 파생 필드 (`user_id == 'USR_00000000'`)
- `author_type` 컬럼 없음

---

## 4. 테이블 의존성 (마이그레이션 순서)

```
com_tn_user
  └── com_tn_user_oauth
  └── com_tn_user_token
  └── com_th_login_log
  └── com_tn_file
        └── com_tn_file_map
  └── cms_tn_board
        └── cms_tn_board_category
        └── cms_tn_post
              └── cms_tn_comment
              └── cms_th_post_history
  └── ai_tn_book
        └── ai_tn_book_page
              └── ai_th_page_revision
              └── ai_th_pipeline_run
com_th_admin_audit_log
```

---

## 5. 비기능 요구사항 (Phase 1 적용)

| 항목 | 요구사항 |
|------|---------|
| 응답 시간 | 일반 API 1초 이내, 번역 파이프라인 제외 |
| 보안 | JWT httpOnly 쿠키, SQL Injection/XSS 방어 |
| 로깅 | OAuth 로그인/실패 → `com_th_login_log` INSERT |
| 파일 크기 | 기본 최대 10MB (게시판 설정으로 조정 가능) |
