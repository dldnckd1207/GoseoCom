# Domain (도메인 모델)

---

| 항목 | 내용 |
|------|------|
| **제품명** | Haedok AI (解讀 AI) |
| **버전** | v2.0 |
| **작성일** | 2026-04-09 (v1.0), 2026-04-14 (v2.0 전면 재작성) |
| **작성자** | - |
| **관련 문서** | [PRD](01_PRD.md), [SRS](02_SRS.md), [Architecture](03_Architecture.md) |

---

## 1. 개요

### 1.1 목적

본 문서는 Haedok AI 시스템의 도메인 모델을 정의한다. 도메인 용어, 핵심 개념과 관계, 엔티티의 개념적 속성, 비즈니스 규칙, Enum/코드값을 포함한다. 물리적 DB 구조는 [ERD](05_ERD.md) 문서를 참조한다.

### 1.2 범위

- 비즈니스 관점의 개념(엔티티) 정의
- 엔티티 간 관계 (개념 수준)
- 비즈니스 규칙 (DB 제약과 무관한 업무 규칙)
- Enum / 코드값 정의

다음은 본 문서의 범위 외이다:
- 컬럼 타입, 제약, 인덱스 → [ERD](05_ERD.md)
- 기능 시나리오 → [SRS](02_SRS.md)
- 시스템 구조 → [Architecture](03_Architecture.md)

### 1.3 도메인 목록

| # | 도메인 | 핵심 엔티티 | 모듈 |
|---|--------|------------|------|
| 1 | **User** | User, UserOAuth | `core/user/` |
| 2 | **File** | File, FileMap | `core/files/` |
| 3 | **Auth** | LoginLog | `auth/` |
| 4 | **Board** | Board, Post, Comment | `board/` |
| 5 | **Translate** | Book, BookPage, PageRevision | `translate/` |
| 6 | **Pipeline** | PipelineRun | `translate/pipeline/` |
| 7 | **Admin Audit** | AdminAuditLog | `core/audit/` |

---

## 2. 도메인 용어집

| 한글 | 영문 | 정의 |
|------|------|------|
| 사용자 | User | OAuth로 가입한 서비스 이용자. AI 시드 계정 포함 |
| OAuth | OAuth | Google/Kakao 소셜 로그인 인증 방식 |
| 권한 레벨 | UserLevel | 사용자의 시스템 접근 수준 (GUEST/USER/ADMIN/SYSTEM_ADMIN) |
| 게시판 | Board | 게시글이 속하는 카테고리 단위. 유형(LIST/IMAGE/QNA)과 설정을 가짐 |
| 게시글 | Post | 사용자가 게시판에 작성하는 글 |
| 댓글 | Comment | 게시글에 달리는 댓글. 사용자 또는 AI 시드 계정이 작성 |
| 파일 | File | 업로드된 파일의 메타정보 |
| 파일 매핑 | FileMap | File과 다양한 엔티티(Post, Comment, BookPage 등)를 연결하는 다형 매핑 |
| 고서 | Old Document | 한문 또는 한글로 작성된 역사적 문서. OCR/번역 대상 |
| 책 | Book | 번역 단위 컨테이너. 1건 이상의 BookPage를 포함 |
| 책 페이지 | BookPage | 이미지 1장에 대한 OCR 결과 및 번역 결과 |
| 번역 수정 이력 | PageRevision | BookPage의 직역/의역 수정 전 버전 (append-only) |
| 직역 | Literal Translation | 원문 글자를 그대로 한글로 대응하여 번역한 결과 |
| 의역 | Free Translation | 원문의 의미를 현대 한국어로 자연스럽게 풀어 번역한 결과 |
| 파이프라인 | Pipeline | OCR → 번역 → 후처리 자동 처리 흐름 |
| 파이프라인 실행 | PipelineRun | 파이프라인 1회 실행 단위. 트리거, 상태, 결과를 가짐 |
| 라이브러리 | Library | 로그인 사용자의 Book 이력 목록 (별도 엔티티 없음, Book 조회) |
| AI 시드 계정 | AI Seed Account | AI 자동 답변을 작성하는 시스템 전용 User (`USR_00000000`) |
| 로그인 로그 | LoginLog | OAuth 로그인 시도/결과 이벤트 기록 |
| 관리자 감사 로그 | AdminAuditLog | 관리자 작업 이력 기록 (Phase 3) |
| 필터링 댓글 | Filtered Comment | AI 검수에서 악성으로 판별되어 숨김 처리된 댓글 (Phase 3) |

---

## 3. 도메인 정의

### 3.1 User 도메인

#### 엔티티

**User** — 시스템에 가입한 사용자. OAuth로만 생성된다. AI 시드 계정(`USR_00000000`)도 User 엔티티로 관리한다.

| 속성 | 설명 |
|------|------|
| id | ID-GEN (`USR_00000001`) |
| email | 로그인 식별자, UNIQUE |
| name | 표시 이름 |
| profile_image_url | 프로필 이미지 (nullable) |
| user_level | 권한 레벨 (기본 USER=10) |
| use_yn | 계정 활성 여부 (기본 true). false 시 로그인 불가 |
| block_yn | 차단 여부 (기본 false). true 시 서비스 이용 불가 |
| blocked_at | 차단 시각 (nullable) |
| blocked_by | 차단한 관리자 user_id (nullable) |
| joined_at | 최초 가입 시각 |
| last_login_at | 최근 로그인 시각 (nullable) |
| left_at | 탈퇴 시각 (nullable) |
| left_reason | 탈퇴 사유 (nullable) |

**관계**:
- UserOAuth (1:N) — 한 User가 Google/Kakao 모두 연결 가능
- Post (1:N) — 작성한 게시글
- Comment (1:N) — 작성한 댓글
- Book (1:N) — 소유한 번역 Book

---

**UserOAuth** — User와 OAuth Provider 간 연결 정보.

| 속성 | 설명 |
|------|------|
| id | ID-GEN (`OAUTH_00000001`) |
| user_id | FK → User |
| provider | `google` \| `kakao` |
| provider_user_id | Provider 측 고유 ID |
| provider_email | Provider에서 받은 이메일 (nullable) |
| del_yn | 삭제 여부 (기본 false) |
| deleted_at | 삭제 시각 (nullable) |
| deleted_by | 삭제자 user_id (nullable) — 본인 탈퇴 또는 관리자 연결 해제 구분 |

**관계**:
- User (N:1)

---

#### Enum

**UserLevel**

| 값 | 상수 | 의미 | Phase |
|----|------|------|-------|
| `0` | `GUEST` | 비로그인 상태 | 1 |
| `10` | `USER` | 일반 사용자 (기본값) | 1 |
| `70` | `ADMIN` | 앱 관리자 (게시판/댓글/게시글 관리) — Admin UI는 Phase 3 | 1 |
| `100` | `SYSTEM_ADMIN` | 시스템 관리자 (로그/설정/파이프라인 관리) — Admin UI는 Phase 3 | 1 |

**UserProvider**

| 값 | 의미 |
|----|------|
| `google` | Google OAuth |
| `kakao` | Kakao OAuth |

---

#### 비즈니스 규칙

| ID | 규칙 | Phase |
|----|------|-------|
| **UBR-01** | OAuth 로그인 시 email 기준으로 User UPSERT, (provider + provider_user_id) 기준으로 UserOAuth UPSERT | 1 |
| **UBR-02** | 개인정보 최소 수집: email, name, profile_image_url만 저장. 전화번호 등 미수집 | 1 |
| **UBR-03** | 신규 User의 user_level 기본값은 USER(10) | 1 |
| **UBR-04** | `use_yn=false` 계정은 로그인 시 거부된다 | 1 |
| **UBR-05** | `block_yn=true` 계정은 로그인은 가능하나 서비스 이용이 제한된다 | 1 |
| **UBR-06** | AI 시드 계정(`USR_00000000`)은 DB seed로 투입되며 삭제/수정 불가 | 1 |
| **UBR-07** | 최초 로그인 시 `INITIAL_ADMIN_EMAILS` 환경변수에 포함된 이메일이면 user_level=100 자동 승격 (1회만) | 3 |
| **UBR-08** | 같은 이메일로 Google/Kakao 모두 로그인하면 동일 User에 UserOAuth가 추가된다 | 1 |
| **UBR-09** | 탈퇴 시 User와 연결된 모든 UserOAuth 레코드를 함께 soft delete 처리한다 | 1 |
| **UBR-10** | 탈퇴 후 3개월 뒤 스케줄러가 email → `deleted_{id}@deleted.com`, name → "탈퇴한 사용자"로 익명화하고 UserOAuth를 hard delete한다 | 1 |
| **UBR-11** | 익명화된 사용자 프로필은 "탈퇴한 사용자"로 표시하며 상세 조회 불가. 게시글/댓글의 `author_name` 스냅샷은 변경하지 않는다 | 1 |

### 3.2 File 도메인

#### 엔티티

**File** — 업로드된 파일의 메타정보. 바이너리는 스토리지에 별도 저장. (참고: `com_tn_file`)

| 속성 | 설명 |
|------|------|
| id | ID-GEN (`FILE_00000001`) |
| original_name | 사용자가 업로드한 원본 파일명 |
| stored_name | 스토리지에 저장된 파일명 (충돌 방지용 UUID 기반) |
| url_path | 웹 접근용 상대 경로 |
| local_path | 서버 내부용 절대 경로 |
| file_size | 파일 크기 (bytes) |
| file_ext | 확장자 |
| mime_type | `image/jpeg`, `image/png` 등 |
| upload_type | 업로드 출처 (`FORM` \| `API`) |
| download_count | 파일 접근 횟수 (기본 0) |
| created_by | 업로드한 user_id (FK → User) |
| del_yn | 삭제 여부 (기본 false) |
| deleted_at | 삭제 시각 (nullable) |
| deleted_by | 삭제한 user_id (nullable) |

**관계**:
- FileMap (1:N) — 다양한 엔티티에 매핑

---

**FileMap** — File과 엔티티를 연결하는 다형 매핑 테이블. (참고: `com_tn_file_map`)

| 속성 | 설명 |
|------|------|
| file_id | FK → File |
| target_type | 대상 엔티티 유형 (`POST` \| `COMMENT` \| `BOOK_PAGE`) |
| target_id | 대상 엔티티 ID |
| file_group | 파일 용도 (`thumbnail` \| `attachment` \| `original`) |
| sort_order | 첨부 순서 (기본 0) |
| created_by | 매핑 생성한 user_id (FK → User) |

> `BookPage ↔ File` 연결은 FileMap 경유 방식(`target_type='BOOK_PAGE'`)으로 잠정 확정. ERD 작업 시 재검토.

**관계**:
- File (N:1)

---

#### Enum

**FileTargetType**

| 값 | 의미 | Phase |
|----|------|-------|
| `POST` | 게시글 첨부 | 1 |
| `COMMENT` | 댓글 첨부 | 1 |
| `BOOK` | Book 원본 업로드 파일 (이미지/PDF) | 1 |

**FileGroup**

| 값 | 의미 |
|----|------|
| `thumbnail` | 썸네일 이미지 |
| `attachment` | 일반 첨부파일 |
| `original` | 원본 이미지 (번역기 업로드 등) |

**UploadType**

| 값 | 의미 |
|----|------|
| `FORM` | 폼 기반 업로드 (게시글 첨부 등) |
| `API` | API 직접 호출 |

---

#### 비즈니스 규칙

| ID | 규칙 | Phase |
|----|------|-------|
| **FBR-01** | 파일 업로드 시 `POST /api/v1/boards/{board_code}/uploads`로 먼저 File 레코드 생성 후 file_id를 반환한다 (선업로드) | 1 |
| **FBR-02** | 엔티티 생성 시 file_id 목록을 전달하여 FileMap을 생성한다 | 1 |
| **FBR-03** | 허용 MIME 타입: 번역기(`ai_tn_book`)는 `image/*` 전용. 게시판(`cms_tn_post`)은 게시판 `attach_ext` 설정에 따라 허용 타입 결정 (PDF 등 가능) | 1 |
| **FBR-04** | 파일 최대 크기는 10MB. 초과 시 거부 | 1 |
| **FBR-05** | 게시판 첨부 시 해당 게시판의 `attach_ext`, `attach_size`, `attach_count` 설정을 추가로 검증한다 | 1 |
| **FBR-06** | 파일 접근은 `GET /files/{uuid}`를 통해서만 허용. 직접 경로 노출 금지 | 1 |
| **FBR-07** | Phase 1 스토리지는 로컬 볼륨. Phase 2 이후 S3 호환으로 전환 가능 (url_path/local_path 분리로 대응) | 1 |

### 3.3 Auth 도메인

#### 엔티티

**LoginLog** — OAuth 로그인 시도/결과 이벤트 기록. 로그성 데이터라 BIGSERIAL PK 사용. (참고: `com_th_login_log`)

| 속성 | 설명 |
|------|------|
| id | BIGSERIAL (로그성) |
| user_id | 로그인 성공 시 FK → User. 실패 시 NULL |
| login_id | 로그인 시도 식별자 (provider email) |
| login_type | `GOOGLE` \| `KAKAO` |
| login_result | `SUCCESS` \| `FAIL` |
| fail_reason | 실패 사유 (nullable) |
| ip_address | 클라이언트 IP |
| client_info | OS/브라우저 정보 (nullable) |
| session_id | JWT 세션 ID (nullable) |
| created_at | 로그인 시도 시각 |

> 로그성 테이블이므로 soft delete 없음. append-only.

---

#### Enum

**LoginType**

| 값 | 의미 |
|----|------|
| `GOOGLE` | Google OAuth |
| `KAKAO` | Kakao OAuth |

**LoginResult**

| 값 | 의미 |
|----|------|
| `SUCCESS` | 로그인 성공 |
| `FAIL` | 로그인 실패 |

---

#### 비즈니스 규칙

| ID | 규칙 | Phase |
|----|------|-------|
| **ABR-01** | OAuth 로그인 시도마다 성공/실패 여부와 무관하게 LoginLog를 INSERT한다 | 1 |
| **ABR-02** | 로그인 실패 시 `user_id`는 NULL, `fail_reason`에 사유를 기록한다 | 1 |
| **ABR-03** | LoginLog는 수정/삭제하지 않는다 (append-only) | 1 |
| **ABR-04** | 조회 UI는 Phase 3 관리자 페이지(SFR-303)에서 제공한다 | 3 |

### 3.4 Board 도메인

#### 엔티티

**Board** — 게시글이 속하는 카테고리 단위. 유형과 기능 설정을 가진다. (참고: `cms_tn_board`)

| 속성 | 설명 |
|------|------|
| id | ID-GEN (`BOARD_00000001`) |
| board_code | URL slug, UNIQUE |
| board_name | 게시판명 |
| board_desc | 게시판 설명 (nullable) |
| board_type | UI 렌더링 유형 (`LIST` \| `IMAGE` \| `QNA`) |
| notice_yn | 공지 기능 사용 여부 |
| reply_yn | 답글 사용 여부 |
| comment_yn | 댓글 사용 여부 |
| secret_yn | 비밀글 사용 여부 (선반영, Phase 3 이후 구현) |
| like_yn | 좋아요 사용 여부 (선반영, Phase 3 이후 구현) |
| attach_yn | 첨부파일 사용 여부 |
| attach_ext | 허용 확장자 목록 (nullable, 예: `jpg,png`) |
| attach_size | 첨부 최대 크기 KB (기본 10240 = 10MB) |
| attach_count | 첨부 최대 개수 (기본 5) |
| list_count | 목록 페이지당 게시글 수 (기본 10) |
| auto_reply_enabled | AI 자동 답변 활성 여부 (기본 false) |
| auto_reply_delay_min | 자동 답변 대기 시간 분 (기본 5) |
| pipeline_enabled | 파이프라인 연동 여부 (기본 false, Phase 2부터 실 동작) |
| sort_order | 목록 정렬 순서 (기본 0) |
| use_yn | 게시판 활성 여부 |
| created_by / updated_by | 생성자 / 수정자 user_id |

**관계**:
- Post (1:N)

---

**Post** — 사용자가 게시판에 작성하는 글. (참고: `cms_tn_post`)

| 속성 | 설명 |
|------|------|
| id | ID-GEN (`POST_00000001`) |
| board_id | FK → Board |
| user_id | FK → User |
| author_name | 작성 시점 이름 스냅샷 |
| parent_id | FK → Post (답글인 경우, nullable) |
| depth | 답글 깊이 (기본 0) |
| title | 제목 |
| content | 본문 |
| notice_yn | 공지 여부 (기본 false) |
| secret_yn | 비밀글 여부 (선반영, Phase 3 이후 구현, 기본 false) |
| view_count | 조회수 (기본 0) |
| like_count | 좋아요 수 (선반영, Phase 3 이후 구현, 기본 0) |
| comment_count | 댓글 수 캐시 (자동 답변 조건 판별용, 기본 0) |
| auto_reply_status | 자동 답변 상태 (`PENDING` \| `COMPLETED` \| `SKIPPED`) |
| auto_reply_at | 자동 답변 처리 시각 (nullable) |
| created_by / updated_by | 생성자 / 수정자 user_id |

**관계**:
- Board (N:1)
- User (N:1)
- Post (N:1, self, 답글)
- Comment (1:N)
- FileMap (1:N, `target_type='POST'`)
- PostHistory (1:N, Phase 1 — 수정·삭제 시 INSERT)

---

**Comment** — 게시글에 달리는 댓글. 사용자 및 AI 시드 계정이 작성한다. (참고: `cms_tn_comment`)

| 속성 | 설명 |
|------|------|
| id | ID-GEN (`CMT_00000001`) |
| post_id | FK → Post |
| user_id | FK → User (AI 시드 계정 포함) |
| author_name | 작성 시점 이름 스냅샷 |
| parent_id | FK → Comment (대댓글, nullable) |
| depth | 댓글 깊이 (기본 0) |
| content | 댓글 내용 |
| like_count | 좋아요 수 (선반영, Phase 3 이후 구현, 기본 0) |
| is_filtered | 악성 판별 여부 (선반영, Phase 3, 기본 false) |
| filter_reason | 판별 사유 (선반영, Phase 3, nullable) |
| filtered_at | 필터링 시각 (선반영, Phase 3, nullable) |
| filter_reviewed_by | 필터 해제한 관리자 user_id (선반영, Phase 3, nullable) |
| created_by / updated_by | 생성자 / 수정자 user_id |

**관계**:
- Post (N:1)
- User (N:1)
- Comment (N:1, self, 대댓글)

---

**PostHistory** — 게시글 수정 이력. (참고: `cms_th_post_history`)

| 속성 | 설명 |
|------|------|
| id | BIGSERIAL (로그성) |
| post_id | FK → Post |
| version | 버전 번호 |
| action | `CREATE` \| `UPDATE` \| `DELETE` \| `ROLLBACK` |
| title | 변경 시점 제목 스냅샷 |
| content | 변경 시점 본문 스냅샷 |
| changed_by | 변경자 user_id |
| changed_at | 변경 시각 |

> Phase 1부터 수정(`UPDATE`)·삭제(`DELETE`) 시 INSERT. 최초 작성(`CREATE`)은 post 테이블 자체로 보존.

---

#### Enum

**BoardType**

| 값 | 의미 | Phase |
|----|------|-------|
| `LIST` | 테이블/리스트 뷰 | 1 |
| `IMAGE` | 카드/갤러리 뷰 | 2 |
| `QNA` | 아코디언 뷰 | 2 |

**PostAutoReplyStatus**

| 값 | 의미 |
|----|------|
| `PENDING` | 자동 답변 대기 |
| `COMPLETED` | 자동 답변 완료 |
| `SKIPPED` | 자동 답변 건너뜀 (댓글 있음 등) |

**PostHistoryAction**

| 값 | 의미 |
|----|------|
| `CREATE` | 최초 작성 |
| `UPDATE` | 수정 |
| `DELETE` | 삭제 |
| `ROLLBACK` | 이전 버전으로 복원 |

---

#### 비즈니스 규칙

| ID | 규칙 | Phase |
|----|------|-------|
| **BBR-01** | 게시글 작성은 로그인 사용자만 가능하다 (`user_level >= USER`) | 1 |
| **BBR-02** | AI 자동 답변 조건: `board.auto_reply_enabled=true` AND `comment_count=0` AND 작성 후 `auto_reply_delay_min` 경과 AND `auto_reply_status=PENDING` | 1 |
| **BBR-03** | AI 자동 답변 댓글의 `user_id`는 AI 시드 계정(`USR_00000000`)이며, `is_ai_gen`으로 판별한다 | 1 |
| **BBR-04** | `comment_count`는 댓글 추가/삭제 시 자동으로 증감한다 (캐시 컬럼) | 1 |
| **BBR-05** | 게시글/댓글 수정·삭제는 본인 또는 ADMIN 이상만 가능하다 | 1 |
| **BBR-06** | `is_filtered=true` 댓글은 삭제되지 않으며 "AI가 감지한 악성 댓글입니다" 로 표시. 사용자가 "내용 보기" 클릭 시 원본 열람 가능 | 3 |
| **BBR-07** | 게시판 파이프라인 연동(`pipeline_enabled=true`)은 Phase 2부터 실 동작 | 2 |
| **BBR-08** | `secret_yn`, `like_yn`, `like_count`는 스키마에 선반영되며 실제 기능은 Phase 3 이후 결정 | 3 |

### 3.5 Translate 도메인

#### 엔티티

**Book** — 번역 단위 컨테이너. Phase 1은 이미지 1장 = Book 1 + Page 1 (QUICK 타입). (테이블: `ai_tn_book`)

| 속성 | 설명 |
|------|------|
| id | ID-Gen (`BOOK_00000001`) |
| owner_user_id | FK → User |
| title | 제목. QUICK 자동 생성: `"빠른 번역 YYYY-MM-DD HH:mm"` |
| book_type | `QUICK` \| `USER_CREATED` |
| source_type | `IMAGE` \| `PDF` |
| total_pages | 전체 페이지 수 (기본 1) |
| status | 번역 진행 상태 |
| is_favorite | 즐겨찾기 여부 (선반영 Phase 1, 활용 Phase 2, 기본 false) |
| share_token | 공유 링크 토큰 (Phase 2, NULL=공유 OFF) |
| summary_text | 요약 텍스트 (Phase 2, nullable) |
| keywords | 키워드 목록 (Phase 2, nullable) |
| *공통 컬럼* | created_at, created_by, updated_at, updated_by |
| *논리 삭제* | del_yn, deleted_at, deleted_by |

**관계**:
- User (N:1) — 소유자
- BookPage (1:N)
- FileMap (1:N, `target_type='BOOK'`) — 원본 업로드 파일 (이미지/PDF)

---

**BookPage** — 이미지 1장에 대한 OCR 결과 및 번역 결과. (테이블: `ai_tn_book_page`)

| 속성 | 설명 |
|------|------|
| id | ID-Gen (`BPAGE_00000001`) |
| book_id | FK → Book |
| page_no | 페이지 번호 |
| ocr_text | OCR 추출 텍스트 |
| ocr_engine | `GOOGLE_VISION` \| `PADDLE` |
| ocr_confidence | OCR 신뢰도 (0.0~1.0, nullable) |
| literal_text | 직역 결과 (nullable) |
| interpretive_text | 의역 결과 (nullable) |
| translator_engine | `GEMINI` \| `CLAUDE` (nullable) |
| status | 페이지 단위 처리 상태 |
| *공통 컬럼* | created_at, created_by, updated_at, updated_by |
| *논리 삭제* | del_yn, deleted_at, deleted_by |

**관계**:
- Book (N:1)
- PageRevision (1:N, Phase 2)

---

**PageRevision** — 번역 수정 전 버전 기록. append-only. Phase 2. (테이블: `ai_th_page_revision`)

| 속성 | 설명 |
|------|------|
| id | Auto Increment (이력 테이블) |
| page_id | FK → BookPage |
| literal_text | 수정 전 직역 스냅샷 |
| interpretive_text | 수정 전 의역 스냅샷 |
| edited_by | FK → User |
| created_at | 수정 시각 |

> 이력 테이블. 수정/삭제 없음 (append-only).

**관계**:
- BookPage (N:1)
- User (N:1)

---

#### Enum

→ §4 Enum 통합 테이블 참조 (BookType, BookSourceType, BookStatus, OcrEngine, TranslatorEngine)

---

#### 비즈니스 규칙

| ID | 규칙 | Phase |
|----|------|-------|
| **TBR-01** | 번역기는 로그인 사용자만 사용 가능하다 (`user_level >= USER`) | 1 |
| **TBR-02** | Phase 1 QUICK Book: 이미지 1장 업로드 시 자동으로 Book + BookPage 1건 생성 | 1 |
| **TBR-03** | QUICK Book 제목은 자동 생성 (`"빠른 번역 YYYY-MM-DD HH:mm"`). 사용자가 이후 수정 가능 | 1 |
| **TBR-04** | 번역 파이프라인은 비동기 실행. `books.status`를 단계별로 업데이트하며 클라이언트는 폴링으로 확인 | 1 |
| **TBR-05** | Phase 1 OCR 엔진은 Google Vision API. GPU 확보 후 PaddleOCR로 전환 (환경변수 `OCR_ENGINE`으로 제어) | 1 |
| **TBR-06** | 번역 수정은 본인 소유 Book의 BookPage만 가능 (`book.owner_user_id == 요청자`) | 2 |
| **TBR-07** | 번역 수정 시 수정 전 내용을 `ai_th_page_revision`에 append-only로 저장 | 2 |
| **TBR-08** | `share_token`은 기본 NULL(공유 OFF). owner가 명시적으로 활성화. 공유 링크는 열람 전용, 비로그인 허용 | 2 |
| **TBR-09** | `is_favorite`, `share_token`은 Phase 1 스키마 선반영, Phase 2부터 활용 | 2 |
| **TBR-10** | `summary_text`, `keywords`는 Phase 2 후처리 파이프라인에서 생성. Book 단위로 저장 | 2 |

---

## 4. Enum / 코드값 통합

> 각 도메인 정의 내 Enum을 여기에 통합 정리한다. 도메인 추가 시 업데이트.

| Enum | 값 | 의미 | 도메인 |
|------|----|------|--------|
| UserLevel | `0` GUEST | 비로그인 | User |
| UserLevel | `10` USER | 일반 사용자 | User |
| UserLevel | `70` ADMIN | 앱 관리자 | User |
| UserLevel | `100` SYSTEM_ADMIN | 시스템 관리자 | User |
| UserProvider | `google` | Google OAuth | User |
| UserProvider | `kakao` | Kakao OAuth | User |
| FileTargetType | `POST` | 게시글 첨부 | File |
| FileTargetType | `COMMENT` | 댓글 첨부 | File |
| FileTargetType | `BOOK` | Book 원본 업로드 파일 (이미지/PDF) | File |
| FileGroup | `thumbnail` | 썸네일 이미지 | File |
| FileGroup | `attachment` | 일반 첨부파일 | File |
| FileGroup | `original` | 원본 이미지 | File |
| UploadType | `FORM` | 폼 기반 업로드 | File |
| UploadType | `API` | API 직접 호출 | File |
| LoginType | `GOOGLE` | Google OAuth | Auth |
| LoginType | `KAKAO` | Kakao OAuth | Auth |
| LoginResult | `SUCCESS` | 로그인 성공 | Auth |
| LoginResult | `FAIL` | 로그인 실패 | Auth |
| BoardType | `LIST` | 테이블/리스트 뷰 | Board |
| BoardType | `IMAGE` | 카드/갤러리 뷰 | Board |
| BoardType | `QNA` | 아코디언 뷰 | Board |
| PostAutoReplyStatus | `PENDING` | 자동 답변 대기 | Board |
| PostAutoReplyStatus | `COMPLETED` | 자동 답변 완료 | Board |
| PostAutoReplyStatus | `SKIPPED` | 자동 답변 건너뜀 | Board |
| PostHistoryAction | `CREATE` | 최초 작성 | Board |
| PostHistoryAction | `UPDATE` | 수정 | Board |
| PostHistoryAction | `DELETE` | 삭제 | Board |
| PostHistoryAction | `ROLLBACK` | 이전 버전 복원 | Board |
| BookType | `QUICK` | 이미지 1장 즉시 번역 | Translate |
| BookType | `USER_CREATED` | 사용자 직접 등록 | Translate |
| BookSourceType | `IMAGE` | 이미지 파일 | Translate |
| BookSourceType | `PDF` | PDF 파일 | Translate |
| BookStatus | `PENDING` | 번역 대기 | Translate |
| BookStatus | `OCR_PROCESSING` | OCR 처리 중 | Translate |
| BookStatus | `TRANSLATING` | 번역 중 | Translate |
| BookStatus | `COMPLETED` | 번역 완료 | Translate |
| BookStatus | `FAILED` | 처리 실패 | Translate |
| OcrEngine | `GOOGLE_VISION` | Google Vision API | Translate |
| OcrEngine | `PADDLE` | PaddleOCR (GPU 확보 후) | Translate |
| TranslatorEngine | `GEMINI` | Gemini Flash | Translate |
| TranslatorEngine | `CLAUDE` | Claude Haiku | Translate |
| PipelineTriggerType | `TRANSLATOR` | 번역기 페이지 트리거 | Pipeline |
| PipelineTriggerType | `AUTO_REPLY` | 자동 답변 스케줄러 트리거 | Pipeline |
| PipelineStatus | `PENDING` | 실행 대기 | Pipeline |
| PipelineStatus | `RUNNING` | 실행 중 | Pipeline |
| PipelineStatus | `COMPLETED` | 정상 완료 | Pipeline |
| PipelineStatus | `FAILED` | 실패 | Pipeline |
| PipelineStatus | `TIMEOUT` | 타임아웃 | Pipeline |

---

## 5. 비즈니스 규칙 통합

> 각 도메인 정의 내 비즈니스 규칙을 여기에 통합 정리한다. 도메인 추가 시 업데이트.

| ID | 규칙 | 도메인 | Phase |
|----|------|--------|-------|
| UBR-01 | OAuth 로그인 시 email 기준 User UPSERT, (provider + provider_user_id) 기준 UserOAuth UPSERT | User | 1 |
| UBR-02 | 개인정보 최소 수집: email, name, profile_image_url만 저장 | User | 1 |
| UBR-03 | 신규 User의 user_level 기본값은 USER(10) | User | 1 |
| UBR-04 | `use_yn=false` 계정은 로그인 시 거부된다 | User | 1 |
| UBR-05 | `block_yn=true` 계정은 로그인은 가능하나 서비스 이용이 제한된다 | User | 1 |
| UBR-06 | AI 시드 계정(`USR_00000000`)은 DB seed로 투입되며 삭제/수정 불가 | User | 1 |
| UBR-07 | 최초 로그인 시 `INITIAL_ADMIN_EMAILS`에 포함된 이메일이면 user_level=100 자동 승격 (1회만) | User | 3 |
| UBR-08 | 같은 이메일로 Google/Kakao 모두 로그인하면 동일 User에 UserOAuth가 추가된다 | User | 1 |
| UBR-09 | 탈퇴 시 User + 연결된 모든 UserOAuth soft delete | User | 1 |
| UBR-10 | 탈퇴 후 3개월 뒤 스케줄러가 email/name 익명화, UserOAuth hard delete | User | 1 |
| UBR-11 | 익명화된 사용자 프로필 "탈퇴한 사용자" 표시, 상세 조회 불가. author_name 스냅샷 변경 없음 | User | 1 |
| FBR-01 | 파일 업로드 시 `POST /api/v1/boards/{board_code}/uploads`로 먼저 File 레코드 생성 후 file_id 반환 (선업로드) | File | 1 |
| FBR-02 | 엔티티 생성 시 file_id 목록을 전달하여 FileMap을 생성한다 | File | 1 |
| FBR-03 | 허용 MIME 타입: 번역기는 `image/*` 전용. 게시판은 `attach_ext` 설정 따름 | File | 1 |
| FBR-04 | 파일 최대 크기 10MB 초과 시 거부 | File | 1 |
| FBR-05 | 게시판 첨부 시 해당 게시판의 `attach_ext`, `attach_size`, `attach_count` 설정을 추가 검증 | File | 1 |
| FBR-06 | 파일 접근은 `GET /files/{uuid}`를 통해서만 허용. 직접 경로 노출 금지 | File | 1 |
| FBR-07 | Phase 1 로컬 볼륨, Phase 2+ S3 호환 전환 가능 (url_path/local_path 분리로 대응) | File | 1 |
| ABR-01 | OAuth 로그인 시도마다 성공/실패 여부와 무관하게 LoginLog를 INSERT한다 | Auth | 1 |
| ABR-02 | 로그인 실패 시 `user_id`는 NULL, `fail_reason`에 사유를 기록한다 | Auth | 1 |
| ABR-03 | LoginLog는 수정/삭제하지 않는다 (append-only) | Auth | 1 |
| ABR-04 | 조회 UI는 Phase 3 관리자 페이지(SFR-303)에서 제공한다 | Auth | 3 |
| BBR-01 | 게시글 작성은 로그인 사용자만 가능 (`user_level >= USER`) | Board | 1 |
| BBR-02 | AI 자동 답변 조건: `auto_reply_enabled=true` AND `comment_count=0` AND 시간 경과 AND `auto_reply_status=PENDING` | Board | 1 |
| BBR-03 | AI 자동 답변 댓글의 `user_id`는 AI 시드 계정(`USR_00000000`), `is_ai_gen`으로 판별 | Board | 1 |
| BBR-04 | `comment_count`는 댓글 추가/삭제 시 자동 증감 (캐시 컬럼) | Board | 1 |
| BBR-05 | 게시글/댓글 수정·삭제는 본인 또는 ADMIN 이상만 가능 | Board | 1 |
| BBR-06 | `is_filtered=true` 댓글은 삭제 안 함. "AI가 감지한 악성 댓글" 표시, "내용 보기"로 원본 열람 | Board | 3 |
| BBR-07 | `pipeline_enabled=true` 게시판의 파이프라인 연동은 Phase 2부터 실 동작 | Board | 2 |
| BBR-08 | `secret_yn`, `like_yn`, `like_count` 스키마 선반영, 실제 구현은 Phase 3 이후 결정 | Board | 3 |
| TBR-01 | 번역기는 로그인 사용자만 사용 가능 (`user_level >= USER`) | Translate | 1 |
| TBR-02 | QUICK Book: 이미지 1장 업로드 시 Book + BookPage 1건 자동 생성 | Translate | 1 |
| TBR-03 | QUICK Book 제목 자동 생성 (`"빠른 번역 YYYY-MM-DD HH:mm"`). 이후 사용자 수정 가능 | Translate | 1 |
| TBR-04 | 번역 파이프라인 비동기 실행. `books.status` 단계별 업데이트, 클라이언트 폴링 | Translate | 1 |
| TBR-05 | Phase 1 OCR: Google Vision API. GPU 확보 후 PaddleOCR 전환 (환경변수 `OCR_ENGINE`) | Translate | 1 |
| TBR-06 | 번역 수정은 본인 소유 Book의 BookPage만 가능 | Translate | 2 |
| TBR-07 | 번역 수정 시 수정 전 내용을 `ai_th_page_revision`에 append-only 저장 | Translate | 2 |
| TBR-08 | `share_token` 기본 NULL(공유 OFF). owner 명시적 활성화. 열람 전용, 비로그인 허용 | Translate | 2 |
| TBR-09 | `is_favorite`, `share_token` Phase 1 선반영, Phase 2부터 활용 | Translate | 2 |
| TBR-10 | `summary_text`, `keywords` Phase 2 후처리에서 생성. Book 단위 저장 | Translate | 2 |
| PBR-01 | 번역기 트리거: `trigger_type=TRANSLATOR`, `book_id` 설정 | Pipeline | 1 |
| PBR-02 | 자동 답변 트리거: `trigger_type=AUTO_REPLY`, `post_id` 설정 | Pipeline | 1 |
| PBR-03 | 파이프라인 실패 시 댓글/번역 결과 등록 안 됨. `status=FAILED` 기록 | Pipeline | 1 |
| PBR-04 | Phase 3 관리자 수동 재실행 가능 (`triggered_by` 기록) | Pipeline | 3 |
| AABR-01 | 관리자(`user_level >= ADMIN`) 작업마다 INSERT | Admin Audit | 3 |
| AABR-02 | `before_data` 변경 전 상태, `after_data` 변경 후 상태 JSON 기록 | Admin Audit | 3 |
| AABR-03 | CREATE는 `before_data=null`, DELETE는 `after_data=null` | Admin Audit | 3 |
| AABR-04 | append-only. 수정/삭제 없음 | Admin Audit | 3 |
| AABR-05 | 조회 UI는 Phase 3 관리자 페이지(SFR-303)에서 제공 | Admin Audit | 3 |

### 3.6 Pipeline 도메인

#### 엔티티

**PipelineRun** — 파이프라인 1회 실행 단위. 트리거, 상태, 결과를 추적한다. (테이블: `ai_th_pipeline_run`, 참고: `com_th_batch_log`)

| 속성 | 설명 |
|------|------|
| id | Auto Increment |
| trigger_type | `TRANSLATOR` \| `AUTO_REPLY` |
| triggered_by | 트리거한 user_id (Phase 3 수동 재실행 시, nullable) |
| book_id | FK → Book (trigger_type=TRANSLATOR, nullable) |
| post_id | FK → Post (trigger_type=AUTO_REPLY, nullable) |
| status | `PENDING` \| `RUNNING` \| `COMPLETED` \| `FAILED` \| `TIMEOUT` |
| started_at | 실행 시작 시각 |
| completed_at | 완료 시각 (nullable) |
| duration_ms | 소요 시간 ms (nullable) |
| total_cnt | 처리 대상 페이지 수 (nullable) |
| success_cnt | 성공 페이지 수 (nullable) |
| fail_cnt | 실패 페이지 수 (nullable) |
| error_msg | 오류 메시지 (nullable) |
| error_stack | 스택트레이스 (nullable) |
| created_at | 생성 시각 |

**관계**:
- Book (N:1, nullable)
- Post (N:1, nullable)

---

#### Enum

**PipelineTriggerType**

| 값 | 의미 | Phase |
|----|------|-------|
| `TRANSLATOR` | 번역기 페이지에서 사용자 트리거 | 1 |
| `AUTO_REPLY` | 게시판 자동 답변 스케줄러 트리거 | 1 |

**PipelineStatus**

| 값 | 의미 |
|----|------|
| `PENDING` | 실행 대기 |
| `RUNNING` | 실행 중 |
| `COMPLETED` | 정상 완료 |
| `FAILED` | 실패 |
| `TIMEOUT` | 타임아웃 |

---

#### 비즈니스 규칙

| ID | 규칙 | Phase |
|----|------|-------|
| **PBR-01** | 번역기 트리거: `trigger_type=TRANSLATOR`, `book_id` 설정 | 1 |
| **PBR-02** | 자동 답변 트리거: `trigger_type=AUTO_REPLY`, `post_id` 설정 | 1 |
| **PBR-03** | 파이프라인 실패 시 댓글/번역 결과 등록 안 됨. `status=FAILED` 기록 | 1 |
| **PBR-04** | Phase 3 관리자 페이지에서 실패한 파이프라인 수동 재실행 가능 (`triggered_by` 기록) | 3 |

### 3.7 Admin Audit 도메인

#### 엔티티

**AdminAuditLog** — 관리자 작업 이력 기록. append-only. (테이블: `com_th_admin_audit_log`, 참고: `com_th_audit_log`)

| 속성 | 설명 |
|------|------|
| id | Auto Increment |
| user_id | FK → User (작업한 관리자) |
| action | 작업 유형 (`BOARD_CREATE`, `POST_DELETE`, `USER_BLOCK` 등) |
| target_type | 대상 엔티티 유형 (`BOARD` \| `POST` \| `COMMENT` \| `USER`, nullable) |
| target_id | 대상 엔티티 ID (nullable) |
| before_data | 변경 전 상태 스냅샷 JSON (nullable) |
| after_data | 변경 후 상태 스냅샷 JSON (nullable) |
| ip_address | 관리자 클라이언트 IP |
| created_at | 작업 시각 |

> Phase 1 스키마 선반영. INSERT는 Phase 3 관리자 페이지 구현 시 시작.

**관계**:
- User (N:1) — 작업한 관리자

---

#### 비즈니스 규칙

| ID | 규칙 | Phase |
|----|------|-------|
| **AABR-01** | 관리자(`user_level >= ADMIN`) 작업마다 INSERT한다 | 3 |
| **AABR-02** | `before_data`에 변경 전 상태, `after_data`에 변경 후 상태를 JSON으로 기록한다 | 3 |
| **AABR-03** | CREATE 작업은 `before_data=null`, DELETE 작업은 `after_data=null` | 3 |
| **AABR-04** | append-only. 수정/삭제 없음 | 3 |
| **AABR-05** | 조회 UI는 Phase 3 관리자 페이지(SFR-303)에서 제공 | 3 |

---

## 6. 변경 이력

| 날짜 | 버전 | 변경 내용 | 작성자 |
|------|------|----------|--------|
| 2026-04-09 | v1.0 | 초안 작성 | - |
| 2026-04-14 | v2.0 | 전면 재작성. 도메인 목록 확정. User/File/Auth/Board/Translate/Pipeline/AdminAudit 전 도메인 정의 완료. ERD 컨벤션 섹션 추가 | - |
