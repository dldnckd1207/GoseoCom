# ERD (Entity Relationship Diagram)

---

| 항목 | 내용 |
|------|------|
| **제품명** | Haedok AI (解讀 AI) |
| **버전** | v1.1 |
| **작성일** | 2026-04-09 (v1.0), 2026-04-14 (v1.1 컨벤션 섹션 추가) |
| **작성자** | - |
| **DB 환경** | PostgreSQL 16+ / SQLAlchemy 2.x / Alembic |
| **관련 문서** | [PRD](01_PRD.md), [SRS](02_SRS.md), [Architecture](03_Architecture.md), [Domain](04_Domain.md) |

---

## 1. 개요

### 1.1 목적

본 문서는 Haedok AI 시스템의 물리적 DB 스키마를 정의한다. 테이블 구조, 컬럼 타입, 제약, 인덱스, 관계, 마이그레이션 전략을 포함한다. 도메인 개념과 비즈니스 규칙은 [Domain](04_Domain.md) 문서를 참조한다.

### 1.2 범위

- 테이블 정의 (컬럼, 타입, 제약, 기본값)
- 관계 정의 (FK, 삭제 정책)
- 인덱스 전략
- 마이그레이션 전략
- Phase별 스키마 변화

### 1.3 관련 문서

- [PRD](01_PRD.md), [SRS](02_SRS.md), [Architecture](03_Architecture.md), [Domain](04_Domain.md)

---

## 2. 명명 및 설계 컨벤션

### 2.1 테이블 명명 패턴

```
[모듈 3자]_[유형 1자][분류 1자]_[테이블명]
```

| 위치 | 값 | 의미 |
|------|-----|------|
| **모듈** | `com` / `cms` / `ai` | 업무 도메인 |
| **유형** | `t` / `v` | Table / View |
| **분류** | `n` / `h` / `m` | Normal / History / Map |

### 2.2 테이블 접두사

| 접두사 | 의미 | 용도 | 예시 |
|--------|------|------|------|
| `com_tn_` | Common Normal | 공통 마스터/업무 | `com_tn_user`, `com_tn_file` |
| `com_th_` | Common History | 공통 이력/로그 | `com_th_login_log`, `com_th_admin_audit_log` |
| `cms_tn_` | CMS Normal | 게시판 업무 | `cms_tn_board`, `cms_tn_post`, `cms_tn_comment` |
| `cms_th_` | CMS History | 게시판 이력 | `cms_th_post_history` |
| `ai_tn_` | AI Normal | AI/번역 업무 | `ai_tn_book`, `ai_tn_book_page` |
| `ai_th_` | AI History | AI/번역 이력 | `ai_th_page_revision`, `ai_th_pipeline_run` |

### 2.3 Haedok AI 테이블 목록

| 테이블명 | 접두사 | ID 전략 | 도메인 |
|---------|--------|---------|--------|
| `com_tn_user` | com_tn_ | ID-Gen | User |
| `com_tn_user_oauth` | com_tn_ | ID-Gen | User |
| `com_tn_user_token` | com_tn_ | ID-Gen | User |
| `com_tn_file` | com_tn_ | ID-Gen | File |
| `com_tn_file_map` | com_tn_ | ID-Gen | File |
| `com_th_login_log` | com_th_ | Auto Increment | Auth |
| `cms_tn_board` | cms_tn_ | ID-Gen | Board |
| `cms_tn_board_category` | cms_tn_ | ID-Gen | Board |
| `cms_tn_post` | cms_tn_ | ID-Gen | Board |
| `cms_tn_comment` | cms_tn_ | ID-Gen | Board |
| `cms_th_post_history` | cms_th_ | Auto Increment | Board |
| `ai_tn_book` | ai_tn_ | ID-Gen | Translate |
| `ai_tn_book_page` | ai_tn_ | ID-Gen | Translate |
| `ai_th_page_revision` | ai_th_ | Auto Increment | Translate |
| `ai_th_pipeline_run` | ai_th_ | Auto Increment | Pipeline |
| `com_th_admin_audit_log` | com_th_ | Auto Increment | Admin Audit |

### 2.4 ID 생성 전략

| 구분 | 전략 | 형식 | 예시 |
|------|------|------|------|
| Normal 테이블 (`tn_`) | ID-Gen | `[PREFIX]_[8자리]` | `USER_00000001` |
| History 테이블 (`th_`) | Auto Increment | BIGSERIAL | `1`, `2`, `3` ... |

**ID-Gen PREFIX 목록**:

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

> AI 에이전트 고정값: `USR_00000000`

### 2.5 컬럼 명명 규칙

| 규칙 | 예시 |
|------|------|
| 소문자 + snake_case | `user_id`, `created_at` |
| PK | `id` |
| FK | `{참조테이블단수}_id` (예: `board_id`, `user_id`) |
| 일시 | `_at` 접미사 (`created_at`, `deleted_at`) |
| 여부 | `_yn` 접미사 (`use_yn`, `del_yn`) |
| 코드 | `_cd` 접미사 (`status_cd`) |

### 2.6 공통 컬럼

**Normal 테이블 공통 (모든 `tn_` 테이블 필수)**:

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `created_at` | TIMESTAMPTZ | 생성일시 (DEFAULT NOW()) |
| `created_by` | VARCHAR(20) | 생성자 user_id |
| `updated_at` | TIMESTAMPTZ | 수정일시 (DEFAULT NOW()) |
| `updated_by` | VARCHAR(20) | 수정자 user_id |

**논리 삭제 컬럼 (필요한 테이블에 추가)**:

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `del_yn` | BOOLEAN | 삭제 여부 (DEFAULT false) |
| `deleted_at` | TIMESTAMPTZ | 삭제일시 (nullable) |
| `deleted_by` | VARCHAR(20) | 삭제자 user_id (nullable) |

**History 테이블** — append-only. `created_at` 외 수정 컬럼 없음.

### 2.7 기타 컨벤션

| 항목 | 규칙 |
|------|------|
| Enum 표현 | `VARCHAR(N)` (PostgreSQL ENUM 타입 미사용) |
| Boolean | `BOOLEAN`, 기본값 명시 |
| 시간대 | UTC 저장, 표시 단계에서 변환 |
| 문자 집합 | UTF-8 |

---

## 3. 테이블 정의

> 공통 컬럼(created_at, created_by, updated_at, updated_by)과 논리 삭제 컬럼(del_yn, deleted_at, deleted_by)은 §2.6 참조.

### 3.1 User 도메인

#### com_tn_user

| 컬럼 | 타입 | NOT NULL | 기본값 | 설명 |
|------|------|:--------:|--------|------|
| id | VARCHAR(20) | ✓ | — | PK, ID-Gen (`USER_`) |
| email | VARCHAR(255) | ✓ | — | UNIQUE |
| name | VARCHAR(100) | ✓ | — | |
| profile_image_url | VARCHAR(500) | | NULL | |
| user_level | INT | ✓ | 10 | |
| use_yn | BOOLEAN | ✓ | true | |
| block_yn | BOOLEAN | ✓ | false | |
| blocked_at | TIMESTAMPTZ | | NULL | |
| blocked_by | VARCHAR(20) | | NULL | FK → com_tn_user.id |
| joined_at | TIMESTAMPTZ | ✓ | NOW() | |
| last_login_at | TIMESTAMPTZ | | NULL | |
| left_at | TIMESTAMPTZ | | NULL | 탈퇴 시각 |
| left_reason | VARCHAR(500) | | NULL | 탈퇴 사유 |
| created_at / created_by | | ✓ | NOW() | 공통 컬럼 |
| updated_at / updated_by | | ✓ | NOW() | 공통 컬럼 |
| del_yn / deleted_at / deleted_by | | ✓/NULL/NULL | false | 논리 삭제 |

**인덱스**:
- `UNIQUE (email)`
- `ix_user_level (user_level)`
- `ix_user_del (del_yn)`
- `ix_user_left (left_at)` — 탈퇴 후 3개월 익명화 스케줄러용

**FK 삭제 정책**: `blocked_by` → RESTRICT

**탈퇴 정책**:
- 탈퇴 즉시: `del_yn=true`, `left_at=NOW()`
- 탈퇴 3개월 후 스케줄러: `email → deleted_{id}@deleted.com`, `name → "탈퇴한 사용자"`, `profile_image_url → NULL`

---

#### com_tn_user_oauth

| 컬럼 | 타입 | NOT NULL | 기본값 | 설명 |
|------|------|:--------:|--------|------|
| id | VARCHAR(20) | ✓ | — | PK, ID-Gen (`OAUTH_`) |
| user_id | VARCHAR(20) | ✓ | — | FK → com_tn_user.id |
| provider | VARCHAR(20) | ✓ | — | `GOOGLE` \| `KAKAO` |
| provider_user_id | VARCHAR(255) | ✓ | — | |
| provider_email | VARCHAR(255) | | NULL | |
| created_at / created_by | | ✓ | NOW() | 공통 컬럼 |
| updated_at / updated_by | | ✓ | NOW() | 공통 컬럼 |
| del_yn | BOOLEAN | ✓ | false | |
| deleted_at | TIMESTAMPTZ | | NULL | |
| deleted_by | VARCHAR(20) | | NULL | 본인 탈퇴 또는 관리자 연결 해제 구분 |

**인덱스**:
- `UNIQUE (provider, provider_user_id)`
- `ix_user_oauth_user (user_id)`

**FK 삭제 정책**: `user_id` → RESTRICT

**탈퇴 정책**:
- 탈퇴 즉시: soft delete (`del_yn=true`)
- 탈퇴 3개월 후 스케줄러: hard delete (물리 삭제)

---

#### com_tn_user_token

Refresh Token 관리 테이블. Refresh Token Rotation 패턴 적용.

| 컬럼 | 타입 | NOT NULL | 기본값 | 설명 |
|------|------|:--------:|--------|------|
| id | VARCHAR(20) | ✓ | — | PK, ID-Gen (`UTKN_`) |
| user_id | VARCHAR(20) | ✓ | — | FK → com_tn_user.id |
| token_hash | VARCHAR(255) | ✓ | — | Refresh Token 해시값 (원문 저장 금지) |
| expires_at | TIMESTAMPTZ | ✓ | — | 만료 일시 |
| is_revoked | BOOLEAN | ✓ | false | 무효화 여부 |
| created_at | TIMESTAMPTZ | ✓ | NOW() | 발급 일시 |
| created_by | VARCHAR(20) | ✓ | — | 발급 user_id |

**인덱스**:
- `ix_user_token_user (user_id)`
- `ix_user_token_hash (token_hash)`
- `ix_user_token_expires (expires_at)`

**FK 삭제 정책**: `user_id` → CASCADE (회원 탈퇴 시 토큰도 삭제)

**Refresh Token Rotation 정책**:
- Refresh Token 사용 시 → 새 token 발급 + 이전 token `is_revoked=true`
- 이미 `is_revoked=true`인 token으로 요청 시 → 탈취로 간주, 해당 user 전체 token 무효화
- 만료된 token은 스케줄러가 주기적으로 hard delete

---

### 3.2 File 도메인

#### com_tn_file

| 컬럼 | 타입 | NOT NULL | 기본값 | 설명 |
|------|------|:--------:|--------|------|
| id | VARCHAR(20) | ✓ | — | PK, ID-Gen (`FILE_`) |
| uuid | UUID | ✓ | gen_random_uuid() | 파일 서빙 식별자, UNIQUE |
| original_name | VARCHAR(255) | ✓ | — | 원본 파일명 |
| stored_name | VARCHAR(255) | ✓ | — | 저장 파일명 (`{uuid}.ext`) |
| url_path | VARCHAR(500) | ✓ | — | 웹 접근용 경로 (`/files/{uuid}`) |
| local_path | VARCHAR(500) | ✓ | — | 서버 내부 경로 (`storage/files/{YYYY}/{MM}/{uuid}.ext`) |
| file_size | BIGINT | ✓ | — | 파일 크기 (bytes) |
| file_ext | VARCHAR(20) | ✓ | — | 확장자 |
| mime_type | VARCHAR(100) | ✓ | — | MIME 타입 |
| upload_type | VARCHAR(20) | ✓ | — | `FORM` \| `API` |
| download_count | INT | ✓ | 0 | 접근 횟수 |
| created_at / created_by | | ✓ | NOW() | 공통 컬럼 (`created_by` = 업로더 user_id) |
| updated_at / updated_by | | ✓ | NOW() | 공통 컬럼 |
| del_yn / deleted_at / deleted_by | | ✓/NULL/NULL | false | 논리 삭제 |

**인덱스**:
- `UNIQUE ix_file_uuid (uuid)`
- `ix_file_del (del_yn)`
- `ix_file_created (created_at)`

---

#### com_tn_file_map

| 컬럼 | 타입 | NOT NULL | 기본값 | 설명 |
|------|------|:--------:|--------|------|
| id | VARCHAR(20) | ✓ | — | PK, ID-Gen (`FMAP_`) |
| file_id | VARCHAR(20) | ✓ | — | FK → com_tn_file.id |
| target_type | VARCHAR(20) | ✓ | — | Enum: `POST` \| `COMMENT` \| `BOOK` (테이블명 아님, 논리 타입) |
| target_id | VARCHAR(20) | ✓ | — | 대상 엔티티 ID — **FK 없음** (다형성 참조, target_type으로 대상 테이블 구분) |
| file_group | VARCHAR(50) | ✓ | — | `thumbnail` \| `attachment` \| `original` |
| sort_order | INT | ✓ | 0 | 첨부 순서 |
| created_at / created_by | | ✓ | NOW() | 공통 컬럼 |
| updated_at / updated_by | | ✓ | NOW() | 공통 컬럼 |
| del_yn | BOOLEAN | ✓ | false | 논리 삭제 |
| deleted_at | TIMESTAMPTZ | | NULL | |
| deleted_by | VARCHAR(20) | | NULL | |

**첨부/탈부착 처리 패턴**:
- 첨부 시: `(file_id, target_type, target_id)` 기준으로 기존 row 있으면 `del_yn=false` UPDATE, 없으면 INSERT
- 탈부착 시: `del_yn=true` Soft Delete

**인덱스**:
- `ix_file_map_target (target_type, target_id)`
- `ix_file_map_file (file_id)`

**FK 삭제 정책**: `file_id` → RESTRICT

---

### 3.3 Auth 도메인

#### com_th_login_log

History 테이블. append-only. 공통 컬럼 중 `created_at`만 포함.

| 컬럼 | 타입 | NOT NULL | 기본값 | 설명 |
|------|------|:--------:|--------|------|
| id | BIGINT | ✓ | AUTO_INCREMENT | PK |
| user_id | VARCHAR(20) | | NULL | FK → com_tn_user.id (실패 시 NULL) |
| login_id | VARCHAR(255) | ✓ | — | 로그인 시도 식별자 (provider email) |
| login_type | VARCHAR(20) | ✓ | — | `GOOGLE` \| `KAKAO` |
| login_result | VARCHAR(20) | ✓ | — | `SUCCESS` \| `FAIL` |
| fail_reason | VARCHAR(255) | | NULL | 실패 사유 |
| ip_address | VARCHAR(50) | ✓ | — | 클라이언트 IP |
| client_info | VARCHAR(500) | | NULL | OS/브라우저 정보 |
| session_id | VARCHAR(255) | | NULL | JWT 세션 ID |
| created_at | TIMESTAMPTZ | ✓ | NOW() | |

> soft delete 없음. append-only.

**인덱스**:
- `ix_login_log_user (user_id)`
- `ix_login_log_created (created_at)`
- `ix_login_log_result (login_result)` — 실패 로그 분석용

**FK 삭제 정책**: `user_id` → RESTRICT (사용자 익명화만, 물리 삭제 없음)

### 3.4 Board 도메인

#### cms_tn_board

| 컬럼 | 타입 | NOT NULL | 기본값 | 설명 |
|------|------|:--------:|--------|------|
| id | VARCHAR(20) | ✓ | — | PK, ID-Gen (`BOARD_`) |
| board_code | VARCHAR(50) | ✓ | — | UNIQUE, URL slug |
| board_name | VARCHAR(100) | ✓ | — | |
| board_desc | VARCHAR(500) | | NULL | |
| board_type | VARCHAR(20) | ✓ | `LIST` | `LIST` \| `IMAGE` \| `QNA` |
| read_yn | BOOLEAN | ✓ | true | 로그인 사용자 글읽기 허용 |
| guest_read_yn | BOOLEAN | ✓ | true | 비회원 글읽기 허용 |
| write_yn | BOOLEAN | ✓ | true | 로그인 사용자 글작성 허용 |
| guest_write_yn | BOOLEAN | ✓ | false | 비회원 글작성 허용 |
| notice_yn | BOOLEAN | ✓ | true | 공지 기능 허용 |
| reply_yn | BOOLEAN | ✓ | false | 답글 허용 |
| comment_yn | BOOLEAN | ✓ | false | 댓글 허용 |
| secret_yn | BOOLEAN | ✓ | false | 비밀글 선반영 (Phase 3 이후 구현) |
| like_yn | BOOLEAN | ✓ | false | 좋아요 선반영 (Phase 3 이후 구현) |
| category_yn | BOOLEAN | ✓ | false | 카테고리 선반영 (Phase 3 이후 구현) |
| attach_yn | BOOLEAN | ✓ | true | |
| attach_ext | VARCHAR(255) | | NULL | 허용 확장자 (예: `jpg,png`) |
| attach_size | INT | ✓ | 10240 | 최대 크기 KB (기본 10MB = 10240KB) |
| attach_count | INT | ✓ | 5 | 최대 첨부 개수 |
| list_count | INT | ✓ | 10 | 페이지당 목록 수 |
| auto_reply_enabled | BOOLEAN | ✓ | false | |
| auto_reply_delay_min | INT | ✓ | 5 | |
| pipeline_enabled | BOOLEAN | ✓ | false | Phase 2부터 실 동작 |
| sort_order | INT | ✓ | 0 | |
| use_yn | BOOLEAN | ✓ | true | |
| created_at / created_by | VARCHAR(20) | ✓ | NOW() | 공통 컬럼 |
| updated_at / updated_by | VARCHAR(20) | ✓ | NOW() | 공통 컬럼 |
| del_yn / deleted_at / deleted_by | VARCHAR(20) | ✓/NULL/NULL | false | 논리 삭제 |

**인덱스**:
- `UNIQUE (board_code)`
- `ix_board_use (use_yn, sort_order)`

---

#### cms_tn_board_category

> 선반영 (Phase 3 이후 구현). 테이블만 생성, Phase 1에서는 데이터 없음.

| 컬럼 | 타입 | NOT NULL | 기본값 | 설명 |
|------|------|:--------:|--------|------|
| id | VARCHAR(20) | ✓ | — | PK, ID-Gen (`BCAT_`) |
| board_id | VARCHAR(20) | ✓ | — | FK → cms_tn_board.id |
| category_name | VARCHAR(100) | ✓ | — | |
| sort_order | INT | ✓ | 0 | |
| use_yn | BOOLEAN | ✓ | true | |
| created_at / created_by | VARCHAR(20) | ✓ | NOW() | 공통 컬럼 |
| updated_at / updated_by | VARCHAR(20) | ✓ | NOW() | 공통 컬럼 |
| del_yn / deleted_at / deleted_by | VARCHAR(20) | ✓/NULL/NULL | false | 논리 삭제 |

**인덱스**:
- `ix_board_category (board_id, use_yn, sort_order)`

**FK 삭제 정책**: `board_id` → RESTRICT

---

#### cms_tn_post

| 컬럼 | 타입 | NOT NULL | 기본값 | 설명 |
|------|------|:--------:|--------|------|
| id | VARCHAR(20) | ✓ | — | PK, ID-Gen (`POST_`) |
| board_id | VARCHAR(20) | ✓ | — | FK → cms_tn_board.id |
| user_id | VARCHAR(20) | ✓ | — | FK → com_tn_user.id |
| author_name | VARCHAR(100) | ✓ | — | 작성 시점 이름 스냅샷 |
| category_id | VARCHAR(20) | | NULL | FK → cms_tn_board_category.id, 선반영 (Phase 3) |
| parent_id | VARCHAR(20) | | NULL | FK → cms_tn_post.id (답글) |
| depth | INT | ✓ | 0 | |
| title | VARCHAR(255) | ✓ | — | |
| content | TEXT | ✓ | — | PostgreSQL TEXT = 무제한 (LONGTEXT 상당) |
| notice_yn | BOOLEAN | ✓ | false | |
| secret_yn | BOOLEAN | ✓ | false | 선반영 |
| view_count | INT | ✓ | 0 | |
| like_count | INT | ✓ | 0 | 선반영 |
| comment_count | INT | ✓ | 0 | 캐시 컬럼 |
| auto_reply_status | VARCHAR(20) | ✓ | `PENDING` | `PENDING` \| `COMPLETED` \| `SKIPPED` |
| auto_reply_at | TIMESTAMPTZ | | NULL | |
| created_at / created_by | VARCHAR(20) | ✓ | NOW() | 공통 컬럼 |
| updated_at / updated_by | VARCHAR(20) | ✓ | NOW() | 공통 컬럼 |
| del_yn / deleted_at / deleted_by | VARCHAR(20) | ✓/NULL/NULL | false | 논리 삭제 |

**인덱스**:
- `ix_post_board (board_id, del_yn, created_at DESC)`
- `ix_post_user (user_id)`
- `ix_post_parent (parent_id)`
- `ix_post_auto_reply (auto_reply_status, created_at)` — 스케줄러용
- `ix_post_notice (board_id, notice_yn)`

**FK 삭제 정책**: `board_id` → RESTRICT, `user_id` → RESTRICT, `parent_id` → RESTRICT, `category_id` → RESTRICT

---

#### cms_tn_comment

| 컬럼 | 타입 | NOT NULL | 기본값 | 설명 |
|------|------|:--------:|--------|------|
| id | VARCHAR(20) | ✓ | — | PK, ID-Gen (`CMT_`) |
| post_id | VARCHAR(20) | ✓ | — | FK → cms_tn_post.id |
| user_id | VARCHAR(20) | ✓ | — | FK → com_tn_user.id |
| author_name | VARCHAR(100) | ✓ | — | 작성 시점 이름 스냅샷 |
| parent_id | VARCHAR(20) | | NULL | FK → cms_tn_comment.id (대댓글) |
| depth | INT | ✓ | 0 | |
| content | TEXT | ✓ | — | |
| like_count | INT | ✓ | 0 | 선반영 |
| is_filtered | BOOLEAN | ✓ | false | 선반영 (Phase 3) |
| filter_reason | VARCHAR(255) | | NULL | 선반영 (Phase 3) |
| filtered_at | TIMESTAMPTZ | | NULL | 선반영 (Phase 3) |
| filter_reviewed_by | VARCHAR(20) | | NULL | FK → com_tn_user.id, 선반영 (Phase 3) |
| created_at / created_by | VARCHAR(20) | ✓ | NOW() | 공통 컬럼 |
| updated_at / updated_by | VARCHAR(20) | ✓ | NOW() | 공통 컬럼 |
| del_yn / deleted_at / deleted_by | VARCHAR(20) | ✓/NULL/NULL | false | 논리 삭제 |

**인덱스**:
- `ix_comment_post (post_id, del_yn, created_at)`
- `ix_comment_user (user_id)`
- `ix_comment_parent (parent_id)`
- `ix_comment_filtered (is_filtered)` — Phase 3 악성댓글 조회용

**FK 삭제 정책**: 모두 RESTRICT

---

#### cms_th_post_history

History 테이블. append-only. Phase 1 선반영.

| 컬럼 | 타입 | NOT NULL | 기본값 | 설명 |
|------|------|:--------:|--------|------|
| id | BIGINT | ✓ | AUTO_INCREMENT | PK |
| post_id | VARCHAR(20) | ✓ | — | FK → cms_tn_post.id |
| version | INT | ✓ | — | 버전 번호 |
| action | VARCHAR(20) | ✓ | — | `CREATE` \| `UPDATE` \| `DELETE` \| `ROLLBACK` |
| title | VARCHAR(255) | ✓ | — | 변경 시점 스냅샷 |
| content | TEXT | ✓ | — | 변경 시점 스냅샷 |
| changed_by | VARCHAR(20) | ✓ | — | FK → com_tn_user.id |
| changed_at | TIMESTAMPTZ | ✓ | NOW() | |

**인덱스**:
- `ix_post_history_post (post_id, changed_at)`

**FK 삭제 정책**: `post_id` → RESTRICT, `changed_by` → RESTRICT

---

### 3.5 Translate 도메인

#### ai_tn_book

| 컬럼 | 타입 | NOT NULL | 기본값 | 설명 |
|------|------|:--------:|--------|------|
| id | VARCHAR(20) | ✓ | — | PK, ID-Gen (`BOOK_`) |
| owner_user_id | VARCHAR(20) | ✓ | — | FK → com_tn_user.id |
| title | VARCHAR(255) | ✓ | — | QUICK 자동 생성: `"빠른 번역 YYYY-MM-DD HH:mm"` |
| book_type | VARCHAR(20) | ✓ | — | `QUICK` \| `USER_CREATED` |
| source_type | VARCHAR(20) | ✓ | — | `IMAGE` \| `PDF` |
| total_pages | INT | ✓ | 1 | |
| status | VARCHAR(20) | ✓ | `PENDING` | `PENDING` \| `OCR_PROCESSING` \| `TRANSLATING` \| `COMPLETED` \| `FAILED` |
| is_favorite | BOOLEAN | ✓ | false | 선반영 (Phase 2) |
| share_token | VARCHAR(100) | | NULL | 선반영 (Phase 2, NULL=공유 OFF) |
| summary_text | TEXT | | NULL | 선반영 (Phase 2) |
| keywords | JSONB | | NULL | 선반영 (Phase 2) |
| created_at / created_by | VARCHAR(20) | ✓ | NOW() | 공통 컬럼 |
| updated_at / updated_by | VARCHAR(20) | ✓ | NOW() | 공통 컬럼 |
| del_yn / deleted_at / deleted_by | VARCHAR(20) | ✓/NULL/NULL | false | 논리 삭제 |

**인덱스**:
- `ix_book_owner (owner_user_id, del_yn, created_at DESC)` — 라이브러리 조회
- `ix_book_status (status)`
- `UNIQUE (share_token)` — NULL은 UNIQUE 미적용 (PostgreSQL 특성)

**FK 삭제 정책**: `owner_user_id` → RESTRICT

---

#### ai_tn_book_page

| 컬럼 | 타입 | NOT NULL | 기본값 | 설명 |
|------|------|:--------:|--------|------|
| id | VARCHAR(20) | ✓ | — | PK, ID-Gen (`BPAGE_`) |
| book_id | VARCHAR(20) | ✓ | — | FK → ai_tn_book.id |
| page_no | INT | ✓ | — | 페이지 번호 |
| ocr_text | TEXT | | NULL | OCR 추출 텍스트 |
| ocr_engine | VARCHAR(20) | | NULL | `GOOGLE_VISION` \| `PADDLE` |
| ocr_confidence | FLOAT | | NULL | 0.0~1.0 |
| literal_text | TEXT | | NULL | 직역 결과 |
| interpretive_text | TEXT | | NULL | 의역 결과 |
| translator_engine | VARCHAR(20) | | NULL | `GEMINI` \| `CLAUDE` |
| status | VARCHAR(20) | ✓ | `PENDING` | 페이지 단위 처리 상태 |
| created_at / created_by | VARCHAR(20) | ✓ | NOW() | 공통 컬럼 |
| updated_at / updated_by | VARCHAR(20) | ✓ | NOW() | 공통 컬럼 |
| del_yn / deleted_at / deleted_by | VARCHAR(20) | ✓/NULL/NULL | false | 논리 삭제 |

**인덱스**:
- `UNIQUE (book_id, page_no)` — 책 내 페이지 번호 중복 방지
- `ix_book_page_book (book_id)`

**FK 삭제 정책**: `book_id` → RESTRICT

---

#### ai_th_page_revision

History 테이블. append-only. Phase 2.

| 컬럼 | 타입 | NOT NULL | 기본값 | 설명 |
|------|------|:--------:|--------|------|
| id | BIGINT | ✓ | AUTO_INCREMENT | PK |
| page_id | VARCHAR(20) | ✓ | — | FK → ai_tn_book_page.id |
| version | INT | ✓ | — | 수정 버전 번호 |
| literal_text | TEXT | ✓ | — | 수정 전 직역 스냅샷 |
| interpretive_text | TEXT | ✓ | — | 수정 전 의역 스냅샷 |
| edited_by | VARCHAR(20) | ✓ | — | FK → com_tn_user.id |
| created_at | TIMESTAMPTZ | ✓ | NOW() | |

**인덱스**:
- `ix_page_revision_page (page_id, version)`

**FK 삭제 정책**: `page_id` → RESTRICT, `edited_by` → RESTRICT

---

### 3.6 Pipeline 도메인

#### ai_th_pipeline_run

History 테이블. `created_at`만 포함 (상태 변경은 컬럼으로 추적).

| 컬럼 | 타입 | NOT NULL | 기본값 | 설명 |
|------|------|:--------:|--------|------|
| id | BIGINT | ✓ | AUTO_INCREMENT | PK |
| trigger_type | VARCHAR(20) | ✓ | — | `TRANSLATOR` \| `AUTO_REPLY` |
| triggered_by | VARCHAR(20) | | NULL | FK → com_tn_user.id (Phase 3 수동 재실행 시) |
| book_id | VARCHAR(20) | | NULL | FK → ai_tn_book.id |
| post_id | VARCHAR(20) | | NULL | FK → cms_tn_post.id |
| status | VARCHAR(20) | ✓ | `PENDING` | `PENDING` \| `RUNNING` \| `COMPLETED` \| `FAILED` \| `TIMEOUT` |
| started_at | TIMESTAMPTZ | | NULL | 실행 시작 시각 |
| completed_at | TIMESTAMPTZ | | NULL | 완료 시각 |
| duration_ms | BIGINT | | NULL | 소요 시간 ms |
| total_cnt | INT | | NULL | 처리 대상 수 |
| success_cnt | INT | | NULL | 성공 수 |
| fail_cnt | INT | | NULL | 실패 수 |
| error_msg | TEXT | | NULL | 오류 메시지 |
| error_stack | TEXT | | NULL | 스택트레이스 |
| created_at | TIMESTAMPTZ | ✓ | NOW() | |

**인덱스**:
- `ix_pipeline_run_book (book_id)`
- `ix_pipeline_run_post (post_id)`
- `ix_pipeline_run_status (status)`
- `ix_pipeline_run_trigger (trigger_type)`
- `ix_pipeline_run_created (created_at)`

**FK 삭제 정책**: `book_id` → RESTRICT, `post_id` → RESTRICT, `triggered_by` → RESTRICT

---

### 3.7 Admin Audit 도메인

#### com_th_admin_audit_log

History 테이블. append-only. Phase 1 스키마 선반영, Phase 3 INSERT 시작.
`user_id`가 작업자를 담으므로 별도 `created_by` 없음.

| 컬럼 | 타입 | NOT NULL | 기본값 | 설명 |
|------|------|:--------:|--------|------|
| id | BIGINT | ✓ | AUTO_INCREMENT | PK |
| user_id | VARCHAR(20) | ✓ | — | FK → com_tn_user.id (작업한 관리자) |
| action | VARCHAR(50) | ✓ | — | `BOARD_CREATE` \| `POST_DELETE` \| `USER_BLOCK` 등 |
| target_type | VARCHAR(50) | | NULL | `BOARD` \| `POST` \| `COMMENT` \| `USER` |
| target_id | VARCHAR(20) | | NULL | 대상 엔티티 ID |
| before_data | JSONB | | NULL | 변경 전 상태 스냅샷 |
| after_data | JSONB | | NULL | 변경 후 상태 스냅샷 |
| ip_address | VARCHAR(50) | ✓ | — | 관리자 클라이언트 IP |
| created_at | TIMESTAMPTZ | ✓ | NOW() | |

**인덱스**:
- `ix_audit_user (user_id)`
- `ix_audit_target (target_type, target_id)`
- `ix_audit_action (action)`
- `ix_audit_created (created_at)`

**FK 삭제 정책**: `user_id` → RESTRICT

---

### 4.2 images

게시글에 첨부되는 이미지.

| 컬럼 | 타입 | NULL | 기본값 | 설명 |
|------|------|------|--------|------|
| `id` | `BIGSERIAL` | NO | - | PK |
| `post_id` | `BIGINT` | YES | NULL | 첨부 게시글 (번역기 업로드는 NULL, Phase 2) |
| `original_filename` | `VARCHAR(255)` | NO | - | 원본 파일명 |
| `storage_path` | `VARCHAR(500)` | NO | - | 스토리지 키/경로 |
| `mime_type` | `VARCHAR(50)` | NO | - | image/jpeg, image/png 등 |
| `file_size` | `BIGINT` | NO | - | 바이트 |
| `created_at` | `TIMESTAMPTZ` | NO | `NOW()` | 업로드 시각 |

**제약**:
- `CHECK (mime_type LIKE 'image/%')` — BR-03
- `CHECK (file_size > 0 AND file_size <= 10485760)` — 10MB 제한 (BR-04)

**인덱스**:
- PK: `id`
- `idx_images_post_id` on (`post_id`)

**FK**:
- `post_id → posts(id) ON DELETE CASCADE`

---

### 4.3 comments

게시글 댓글.

| 컬럼 | 타입 | NULL | 기본값 | 설명 |
|------|------|------|--------|------|
| `id` | `BIGSERIAL` | NO | - | PK |
| `post_id` | `BIGINT` | NO | - | 부모 게시글 |
| `user_id` | `BIGINT` | YES | NULL | 작성자 (Phase 3, `author_type=user`인 경우) |
| `pipeline_run_id` | `BIGINT` | YES | NULL | `author_type=ai_pipeline`인 경우 결과 생성 실행 |
| `author_type` | `VARCHAR(20)` | NO | `'user'` | `user` / `ai_auto` / `ai_pipeline` |
| `content` | `TEXT` | NO | - | 댓글 본문 |
| `is_filtered` | `BOOLEAN` | NO | `FALSE` | Phase 3, AI 필터링 결과 (BR-09) |
| `created_at` | `TIMESTAMPTZ` | NO | `NOW()` | 작성 시각 |

**제약**:
- `CHECK (author_type IN ('user', 'ai_auto', 'ai_pipeline'))`

**인덱스**:
- PK: `id`
- `idx_comments_post_id` on (`post_id`, `created_at`) — 게시글 상세 조회
- `idx_comments_filtered` on (`is_filtered`) — Phase 3 검수용

**FK**:
- `post_id → posts(id) ON DELETE CASCADE`
- `pipeline_run_id → pipeline_runs(id) ON DELETE SET NULL`
- (Phase 3) `user_id → users(id) ON DELETE SET NULL`

---

### 4.4 ocr_results

OCR 추출 결과.

| 컬럼 | 타입 | NULL | 기본값 | 설명 |
|------|------|------|--------|------|
| `id` | `BIGSERIAL` | NO | - | PK |
| `image_id` | `BIGINT` | NO | - | 입력 이미지 |
| `extracted_text` | `TEXT` | NO | - | OCR 추출 텍스트 |
| `engine` | `VARCHAR(30)` | NO | - | `paddleocr` / `google_vision` |
| `confidence` | `NUMERIC(4,3)` | YES | NULL | 0.000 ~ 1.000 |
| `created_at` | `TIMESTAMPTZ` | NO | `NOW()` | 처리 시각 |

**제약**:
- `CHECK (engine IN ('paddleocr', 'google_vision'))`
- `CHECK (confidence IS NULL OR (confidence >= 0 AND confidence <= 1))`

**인덱스**:
- PK: `id`
- `idx_ocr_results_image_id` on (`image_id`)

**FK**:
- `image_id → images(id) ON DELETE CASCADE`

---

### 4.5 translations

번역 결과 (직역 + 의역).

| 컬럼 | 타입 | NULL | 기본값 | 설명 |
|------|------|------|--------|------|
| `id` | `BIGSERIAL` | NO | - | PK |
| `ocr_result_id` | `BIGINT` | YES | NULL | OCR 결과 (번역기 텍스트 직접 입력은 NULL, Phase 2) |
| `literal` | `TEXT` | NO | - | 직역 |
| `free` | `TEXT` | NO | - | 의역 |
| `model` | `VARCHAR(30)` | NO | - | `gemini_flash` / `claude_haiku` |
| `is_user_edited` | `BOOLEAN` | NO | `FALSE` | 사용자 수정 여부 (BR-07) |
| `created_at` | `TIMESTAMPTZ` | NO | `NOW()` | 처리 시각 |
| `updated_at` | `TIMESTAMPTZ` | NO | `NOW()` | 수정 시각 |

**제약**:
- `CHECK (model IN ('gemini_flash', 'claude_haiku'))`

**인덱스**:
- PK: `id`
- `idx_translations_ocr_result_id` on (`ocr_result_id`)

**FK**:
- `ocr_result_id → ocr_results(id) ON DELETE CASCADE`

---

### 4.6 pipeline_runs

파이프라인 실행 단위.

| 컬럼 | 타입 | NULL | 기본값 | 설명 |
|------|------|------|--------|------|
| `id` | `BIGSERIAL` | NO | - | PK |
| `post_id` | `BIGINT` | YES | NULL | `trigger=post_image`인 경우 |
| `image_id` | `BIGINT` | YES | NULL | 처리한 이미지 |
| `ocr_result_id` | `BIGINT` | YES | NULL | 생성된 OCR 결과 |
| `translation_id` | `BIGINT` | YES | NULL | 생성된 번역 결과 |
| `trigger` | `VARCHAR(20)` | NO | - | `post_image` / `translator` |
| `status` | `VARCHAR(20)` | NO | `'pending'` | `pending` / `running` / `completed` / `failed` |
| `error_message` | `TEXT` | YES | NULL | 실패 시 원인 (BR-11) |
| `started_at` | `TIMESTAMPTZ` | YES | NULL | 실행 시작 시각 |
| `completed_at` | `TIMESTAMPTZ` | YES | NULL | 실행 종료 시각 |
| `created_at` | `TIMESTAMPTZ` | NO | `NOW()` | 레코드 생성 시각 |

**제약**:
- `CHECK (trigger IN ('post_image', 'translator'))`
- `CHECK (status IN ('pending', 'running', 'completed', 'failed'))`

**인덱스**:
- PK: `id`
- `idx_pipeline_runs_status` on (`status`, `created_at`) — 모니터링/재시도
- `idx_pipeline_runs_post_id` on (`post_id`)

**FK**:
- `post_id → posts(id) ON DELETE CASCADE`
- `image_id → images(id) ON DELETE SET NULL`
- `ocr_result_id → ocr_results(id) ON DELETE SET NULL`
- `translation_id → translations(id) ON DELETE SET NULL`

---

### 4.7 summaries — Phase 2

번역 결과의 요약/키워드/빈도수.

| 컬럼 | 타입 | NULL | 기본값 | 설명 |
|------|------|------|--------|------|
| `id` | `BIGSERIAL` | NO | - | PK |
| `translation_id` | `BIGINT` | NO | - | 대상 번역 |
| `summary_text` | `TEXT` | NO | - | 2~5줄 핵심 요약 |
| `keywords` | `JSONB` | NO | `'[]'::jsonb` | 키워드 목록 |
| `word_frequency` | `JSONB` | NO | `'{}'::jsonb` | 단어:빈도 매핑 |
| `model` | `VARCHAR(30)` | NO | - | 사용 AI 모델 |
| `created_at` | `TIMESTAMPTZ` | NO | `NOW()` | 처리 시각 |

**인덱스**:
- PK: `id`
- `uq_summaries_translation_id` UNIQUE on (`translation_id`)

**FK**:
- `translation_id → translations(id) ON DELETE CASCADE`

---

### 4.8 users — Phase 3

사용자.

| 컬럼 | 타입 | NULL | 기본값 | 설명 |
|------|------|------|--------|------|
| `id` | `BIGSERIAL` | NO | - | PK |
| `email` | `VARCHAR(255)` | NO | - | 로그인 식별자 |
| `password_hash` | `VARCHAR(255)` | NO | - | (인증 방식은 Phase 3 SRS에서 확정) |
| `display_name` | `VARCHAR(50)` | NO | - | 표시 이름 |
| `role` | `VARCHAR(20)` | NO | `'user'` | `user` / `admin` |
| `created_at` | `TIMESTAMPTZ` | NO | `NOW()` | 가입 시각 |
| `updated_at` | `TIMESTAMPTZ` | NO | `NOW()` | 수정 시각 |

**제약**:
- `CHECK (role IN ('user', 'admin'))`

**인덱스**:
- PK: `id`
- `uq_users_email` UNIQUE on (`email`)

---

### 4.9 admin_settings — Phase 3

시스템 전역 설정 (Singleton).

| 컬럼 | 타입 | NULL | 기본값 | 설명 |
|------|------|------|--------|------|
| `id` | `SMALLINT` | NO | `1` | 항상 1 (Singleton) |
| `auto_reply_delay_minutes` | `INTEGER` | NO | `5` | 자동 답변 대기 시간 |
| `malicious_check_interval_minutes` | `INTEGER` | NO | `10` | 악성 댓글 검수 주기 |
| `pipeline_enabled` | `BOOLEAN` | NO | `TRUE` | 파이프라인 전역 ON/OFF |
| `updated_at` | `TIMESTAMPTZ` | NO | `NOW()` | 수정 시각 |

**제약**:
- `CHECK (id = 1)` — Singleton 강제
- `PRIMARY KEY (id)`

---

## 5. 인덱스 전략 요약

| 인덱스 | 테이블 | 컬럼 | 용도 |
|--------|--------|------|------|
| `idx_posts_created_at` | posts | (`created_at DESC`) | 게시글 목록 페이지네이션 |
| `idx_posts_auto_reply` | posts | (`auto_reply_status`, `created_at`) | 자동 답변 스케줄러 조회 |
| `idx_images_post_id` | images | (`post_id`) | 게시글 첨부 이미지 조회 |
| `idx_comments_post_id` | comments | (`post_id`, `created_at`) | 게시글 상세 댓글 조회 |
| `idx_comments_filtered` | comments | (`is_filtered`) | 필터링 댓글 조회 (Phase 3) |
| `idx_ocr_results_image_id` | ocr_results | (`image_id`) | 이미지별 OCR 결과 조회 |
| `idx_translations_ocr_result_id` | translations | (`ocr_result_id`) | OCR 결과의 번역 조회 |
| `idx_pipeline_runs_status` | pipeline_runs | (`status`, `created_at`) | 실패/대기 실행 모니터링 |
| `idx_pipeline_runs_post_id` | pipeline_runs | (`post_id`) | 게시글별 실행 이력 |
| `uq_summaries_translation_id` | summaries | (`translation_id`) | Translation:Summary 1:1 강제 |
| `uq_users_email` | users | (`email`) | 로그인 식별자 |

---

## 6. 관계 매핑 요약

| From | To | 관계 | 삭제 정책 |
|------|----|------|----------|
| posts | images | 1:N | CASCADE |
| posts | comments | 1:N | CASCADE |
| posts | pipeline_runs | 1:N | CASCADE |
| images | ocr_results | 1:N (사실상 1:1) | CASCADE |
| ocr_results | translations | 1:N | CASCADE |
| pipeline_runs | comments | 1:1 | SET NULL (댓글 보존) |
| pipeline_runs | images | N:1 | SET NULL |
| pipeline_runs | ocr_results | 1:1 | SET NULL |
| pipeline_runs | translations | 1:1 | SET NULL |
| translations | summaries | 1:1 | CASCADE |
| users | posts | 1:N (Phase 3) | SET NULL |
| users | comments | 1:N (Phase 3) | SET NULL |

---

## 7. 마이그레이션 전략

### 7.1 도구

- **Alembic** (SQLAlchemy 2.x 기반)
- 마이그레이션 파일은 `apps/server/alembic/versions/`에 보관

### 7.2 Phase별 마이그레이션 분리

| Phase | 마이그레이션 | 포함 변경 |
|-------|-------------|----------|
| Phase 1 | `0001_initial.py` | posts, images, comments, ocr_results, translations, pipeline_runs 생성 |
| Phase 2 | `0002_phase2_summaries.py` | summaries 추가, translations에 공유 식별자 검토 |
| Phase 3 | `0003_phase3_users.py` | users 추가, posts/comments에 user_id FK 활성화 |
| Phase 3 | `0004_phase3_admin_settings.py` | admin_settings 추가, comments.is_filtered 본격 사용 |

### 7.3 다운 마이그레이션

- 개발 단계에서는 다운 마이그레이션을 작성하지만, 운영에서는 사용을 지양한다 (데이터 손실 방지).
- 운영 변경은 `forward only`를 원칙으로 한다.

### 7.4 시드 데이터

- Phase 1: 시드 없음
- Phase 3: `admin_settings` 1행 INSERT (`id=1`, 기본값으로)

---

## 8. Phase별 스키마 변화

### Phase 1
- 6개 테이블: `posts`, `images`, `comments`, `ocr_results`, `translations`, `pipeline_runs`
- `posts.user_id`, `comments.user_id`는 컬럼만 존재, FK 제약은 미적용 (NULL 허용)
- `comments.is_filtered`는 컬럼 존재, 기본 `FALSE`로 사실상 미사용

### Phase 2
- `summaries` 테이블 추가
- 번역 결과 공유 링크 요구사항(SFR-203)에 따라 `translations`에 공유 식별자 컬럼 추가 검토

### Phase 3
- `users` 테이블 추가
- `posts.user_id`, `comments.user_id`에 FK 제약 활성화
- `admin_settings` 테이블 추가 (Singleton)
- 악성댓글 필터링 기능에 따라 `comments.is_filtered` 본격 사용

---

## 9. 변경 이력

| 날짜 | 버전 | 변경 내용 | 작성자 |
|------|------|----------|--------|
| 2026-04-09 | v1.0 | 초안 작성 (PRD/SRS/Architecture/Domain 기반) | - |
