---
tags: [spec]
cssclasses:
  - my_style_width_100
status: active
created: 2026-04-19 00:00
updated: 2026-04-19 00:00
parent: "[[SRS_P1]]"
domain: "[[04_Domain]]"
requirement: "SFR-105"
---

# SFR-105 — 게시판 관리 (다중 게시판)

> [!note] 이 문서는 왜 작성하는가
> 하나의 기능을 어떻게 설계하고 구현할지 정리하는 문서.
> "결정 사항" 테이블에 왜 이 방식을 선택했는지 기록하는 것이 핵심이다.
> 이 문서가 나중에 포트폴리오와 회고의 기반이 된다.

---

## 배경

서비스는 공지사항, 자유게시판, QnA 등 다양한 성격의 게시판을 운영한다.
각 게시판은 댓글 허용 여부, 첨부 파일 정책, AI 자동 답변 활성화 등 독립적인 설정을 가진다.
게시판 생성/수정/삭제는 ADMIN 이상 권한만 가능하며, 조회는 누구나 가능하다.
Phase 1에서는 서버(FastAPI)와 어드민 UI 없이 Alembic seed 또는 직접 API 호출로 게시판을 설정한다.

---

## 기능 설명

- `board_code`(slug)로 게시판을 식별한다.
- 게시판 타입은 `LIST` / `IMAGE` / `QNA` 세 가지이며, 타입에 따라 프론트 렌더링 방식이 달라진다.
- 첨부 파일 정책(허용 확장자, 최대 크기, 최대 개수)을 게시판별로 독립 설정한다.
- AI 자동 답변(`auto_reply_enabled`) 플래그로 SFR-104와 연동한다.
- `sort_order` 필드로 게시판 목록 노출 순서를 제어한다.

---

## 핵심 흐름

### 게시판 목록 조회 흐름 (GUEST/USER — `/api/v1/`)

```
1. 클라이언트 → POST /api/v1/boards/list
2. 서버 → 토큰 확인 (Optional)
   - 비회원: guest_read_yn=true 필터 적용
   - 로그인: read_yn=true 필터 적용
3. 서버 → use_yn=true, del_yn=false + sort_order ASC 정렬
4. 서버 → 경량 board 목록 반환 (200 SUCCESS)
```

### 게시판 단건 조회 흐름 (GUEST/USER — `/api/v1/`)

```
1. 클라이언트 → GET /api/v1/boards/{board_code}
2. 서버 → board 존재 확인 (del_yn=false, use_yn=true)
3. 없으면 → 404 BOARD_NOT_FOUND
4. 서버 → 토큰 확인 (Optional)
   - 비회원 + guest_read_yn=false → 403 FORBIDDEN
5. 서버 → 전체 설정 포함 board 반환 (200 SUCCESS)
```

### 게시판 목록 조회 흐름 (ADMIN — `/admin/api/v1/`)

```
1. ADMIN → POST /admin/api/v1/boards/list
2. 서버 → del_yn 필터 없음 (비활성/삭제 포함 전체 조회)
3. 서버 → use_yn, keyword 등 검색 조건 적용 (optional)
4. 서버 → sort_order ASC 정렬
5. 서버 → 전체 설정 포함 board 목록 반환 (200 SUCCESS)
```

### 게시판 단건 조회 흐름 (ADMIN — `/admin/api/v1/`)

```
1. ADMIN → GET /admin/api/v1/boards/{board_id}
2. 서버 → board 존재 확인 (del_yn 무관)
3. 없으면 → 404 BOARD_NOT_FOUND
4. 서버 → 전체 설정 포함 board 반환 (200 SUCCESS)
```

### 게시판 생성 흐름 (ADMIN — `/admin/api/v1/`)

```
1. ADMIN → POST /admin/api/v1/boards
2. 서버 → board_code 중복 확인
3. 중복이면 → 409 BOARD_CODE_ALREADY_EXISTS
4. 서버 → cms_tn_board INSERT (ID-Gen: BRD_XXXXXXXX)
5. 서버 → 생성된 board 반환 (201 CREATED)
```

### 게시판 수정 흐름 (ADMIN — `/admin/api/v1/`)

```
1. ADMIN → PUT /admin/api/v1/boards/{board_id}
2. 서버 → board 존재 확인 (del_yn=false)
3. 없으면 → 404 BOARD_NOT_FOUND
4. 서버 → board_code 변경 요청이면 중복 확인
5. 서버 → cms_tn_board UPDATE
6. 서버 → 수정된 board 반환 (200 UPDATED)
```

### 게시판 삭제 흐름 (ADMIN — `/admin/api/v1/`)

```
1. ADMIN → DELETE /admin/api/v1/boards/{board_id}
2. 서버 → board 존재 확인
3. 서버 → 해당 board에 연결된 post 존재 여부 확인
4. post가 있으면 → 409 BOARD_HAS_POSTS (물리 삭제 불가)
5. post가 없으면 → del_yn=true Soft Delete
6. 서버 → 200 DELETED
```

---

## 설계

### 구조

- **영향 받는 레이어**: Router → Service → Repository
- **신규 생성**:
  - `app/board/models.py`
  - `app/board/schemas.py`
  - `app/board/repository.py`
  - `app/board/service.py`
  - `app/board/router.py` — 클라이언트 API (`/api/v1/boards/`)
  - `app/board/admin_router.py` — 관리자 API (`/admin/api/v1/boards/`)
- **변경 대상**: `app/main.py` (board router 등록)
- **의존성**: SFR-108 인증 모듈 (`@require_level`)

### 데이터

#### cms_tn_board

| 컬럼 | 타입 | NOT NULL | 기본값 | 설명 |
|------|------|:--------:|--------|------|
| id | VARCHAR(20) | ✓ | — | PK, ID-Gen (`BRD_`) |
| board_code | VARCHAR(50) | ✓ | — | UNIQUE, URL slug |
| board_name | VARCHAR(100) | ✓ | — | |
| board_desc | VARCHAR(500) | | NULL | |
| board_type | VARCHAR(20) | ✓ | `LIST` | `LIST` \| `IMAGE` \| `QNA` |
| read_yn | BOOLEAN | ✓ | true | 로그인 사용자 글읽기 허용 |
| guest_read_yn | BOOLEAN | ✓ | true | 비회원 글읽기 허용 |
| write_yn | BOOLEAN | ✓ | true | 로그인 사용자 글작성 허용 |
| guest_write_yn | BOOLEAN | ✓ | false | 비회원 글작성 허용 |
| notice_yn | BOOLEAN | ✓ | true | 공지 기능 허용 여부 |
| reply_yn | BOOLEAN | ✓ | false | 답글(대댓글) 허용 여부 |
| comment_yn | BOOLEAN | ✓ | false | 댓글 허용 여부 |
| secret_yn | BOOLEAN | ✓ | false | 비밀글 (Phase 3 이후 구현) |
| like_yn | BOOLEAN | ✓ | false | 좋아요 (Phase 3 이후 구현) |
| category_yn | BOOLEAN | ✓ | false | 카테고리 (Phase 3 이후 구현) |
| attach_yn | BOOLEAN | ✓ | true | 첨부 파일 허용 여부 |
| attach_ext | VARCHAR(255) | | NULL | 허용 확장자 (예: `jpg,png,pdf`) |
| attach_size | INT | ✓ | 10240 | 최대 크기 KB (기본 10MB) |
| attach_count | INT | ✓ | 5 | 첨부 최대 개수 |
| list_count | INT | ✓ | 10 | 페이지당 목록 수 |
| auto_reply_enabled | BOOLEAN | ✓ | false | AI 자동 답변 (SFR-104 연동) |
| auto_reply_delay_min | INT | ✓ | 5 | 자동 답변 딜레이 (분) |
| pipeline_enabled | BOOLEAN | ✓ | false | Phase 2 이후 실 동작 |
| sort_order | INT | ✓ | 0 | 목록 노출 순서 |
| use_yn | BOOLEAN | ✓ | true | 활성 여부 |
| created_at | TIMESTAMPTZ | ✓ | NOW() | |
| created_by | VARCHAR(20) | ✓ | — | FK → com_tn_user.id |
| updated_at | TIMESTAMPTZ | ✓ | NOW() | |
| updated_by | VARCHAR(20) | ✓ | — | FK → com_tn_user.id |
| del_yn | BOOLEAN | ✓ | false | |
| deleted_at | TIMESTAMPTZ | | NULL | |
| deleted_by | VARCHAR(20) | | NULL | FK → com_tn_user.id |

**인덱스:**
- `UNIQUE (board_code)`
- `ix_board_use (use_yn, sort_order)`

### 인터페이스

**API**

**클라이언트 API (`/api/v1/`) — GUEST/USER**

| Method | Path | 설명 | 인증 |
|--------|------|------|------|
| POST | `/api/v1/boards/list` | 게시판 목록 조회 (경량) | Optional |
| GET | `/api/v1/boards/{board_code}` | 게시판 단건 조회 (전체 설정) | Optional |

> Optional 인증: 비회원이면 `guest_read_yn=true` 게시판만, 로그인 사용자면 `read_yn=true` 게시판 반환.

**관리자 API (`/admin/api/v1/`) — ADMIN 전용 (`admin_router.py`, Phase 1 구현 / Phase 3 UI 연동)**

| Method | Path | 설명 | 인증 |
|--------|------|------|------|
| POST | `/admin/api/v1/boards/list` | 게시판 전체 목록 (비활성 포함) | ADMIN |
| GET | `/admin/api/v1/boards/{board_id}` | 게시판 단건 조회 | ADMIN |
| POST | `/admin/api/v1/boards` | 게시판 생성 | ADMIN |
| PUT | `/admin/api/v1/boards/{board_id}` | 게시판 수정 | ADMIN |
| DELETE | `/admin/api/v1/boards/{board_id}` | 게시판 삭제 (Soft) | ADMIN |

> Phase 1에서 API 구현 완료. Phase 1은 admin UI 없으므로 Swagger로 관리. Phase 3에서 admin UI 연동 및 디테일 보완.

**클라이언트 API 스키마**

`POST /api/v1/boards/list` 요청:
```json
{
  "page": 1,
  "size": 20
}
```

`POST /api/v1/boards/list` 응답 (경량 — 탭 렌더링용):
```json
{
  "header": { "success": true, "code": "SUCCESS", "message": "요청이 성공적으로 처리되었습니다." },
  "body": {
    "data": {
      "items": [
        {
          "id": "BRD_00000001",
          "board_code": "translation",
          "board_name": "번역",
          "board_type": "LIST",
          "guest_read_yn": true,
          "sort_order": 0,
          "use_yn": true
        }
      ],
      "total": 3,
      "page": 1,
      "size": 20
    }
  }
}
```

`GET /api/v1/boards/{board_code}` 응답 (전체 설정 — 게시판 진입 시):
```json
{
  "header": { "success": true, "code": "SUCCESS", "message": "요청이 성공적으로 처리되었습니다." },
  "body": {
    "data": {
      "id": "BRD_00000001",
      "board_code": "translation",
      "board_name": "번역",
      "board_desc": "번역 관련 게시판입니다.",
      "board_type": "LIST",
      "read_yn": true,
      "guest_read_yn": true,
      "write_yn": true,
      "guest_write_yn": false,
      "notice_yn": true,
      "reply_yn": false,
      "comment_yn": true,
      "attach_yn": true,
      "attach_ext": "jpg,png,pdf",
      "attach_size": 10240,
      "attach_count": 5,
      "list_count": 20,
      "auto_reply_enabled": false,
      "sort_order": 0,
      "use_yn": true
    }
  }
}
```

**관리자 API 스키마**

`POST /admin/api/v1/boards` 요청 (생성):
```json
{
  "board_code": "free",
  "board_name": "자유게시판",
  "board_desc": "자유롭게 글을 작성하세요.",
  "board_type": "LIST",
  "read_yn": true,
  "guest_read_yn": true,
  "write_yn": true,
  "guest_write_yn": false,
  "notice_yn": true,
  "reply_yn": false,
  "comment_yn": true,
  "attach_yn": true,
  "attach_ext": "jpg,png,pdf",
  "attach_size": 10240,
  "attach_count": 5,
  "list_count": 20,
  "auto_reply_enabled": false,
  "auto_reply_delay_min": 5,
  "sort_order": 1
}
```

`POST /admin/api/v1/boards/list` 요청 (전체 목록):
```json
{
  "keyword": null,
  "use_yn": null,
  "page": 1,
  "size": 20
}
```

`PUT /admin/api/v1/boards/{board_id}` 요청 (수정, 변경 필드만):
```json
{
  "board_name": "번역 게시판",
  "comment_yn": true,
  "sort_order": 0
}
```

**에러 응답**

| 상황 | HTTP | code |
|------|------|------|
| 권한 없음 | 403 | `FORBIDDEN` |
| board_code 중복 | 409 | `BOARD_CODE_ALREADY_EXISTS` |
| 게시판 없음 | 404 | `BOARD_NOT_FOUND` |
| 비회원이 guest_read_yn=false 게시판 접근 | 403 | `FORBIDDEN` |
| 게시글 있는 게시판 삭제 시도 | 409 | `BOARD_HAS_POSTS` |

---

## 결정 사항

| 주제 | 선택 | 이유 (트레이드오프 포함) | 검토한 대안 |
|------|------|--------------------------|-------------|
| 게시판 식별자 | `board_code` (slug) + `id` (PK) 병행 | URL을 `/boards/free` 형태로 사람이 읽을 수 있게 유지. `id`는 내부 FK용 | id만 사용(URL 가독성 낮음), slug만 사용(변경 시 FK 대응 복잡) |
| 삭제 방식 | Soft Delete (`del_yn=true`) | 게시글이 연결된 게시판 물리 삭제 시 FK 위반 및 게시글 고아화 방지 | Hard Delete(데이터 복구 불가, FK 오류 위험) |
| 게시글 있는 게시판 삭제 | 409 반환 | 연결된 게시글 보호. 필요 시 게시판 비활성화(`use_yn=false`)로 대체 | 게시글 cascade 삭제(데이터 손실 위험) |
| ADMIN 전용 CUD | `@require_level(UserRole.ADMIN)` | Phase 1은 관리자 UI 없음. API로만 설정 관리 | 별도 관리자 서버(오버엔지니어링) |
| Phase 3 선반영 컬럼 | `secret_yn`, `like_yn` 컬럼 포함 | ERD 확정 사항. 마이그레이션 비용 최소화. Phase 1 API에서는 설정 불가(고정 false) | Phase 3 때 추가(마이그레이션 추가 필요) |
| `attach_ext` 저장 형식 | CSV 문자열 (예: `"jpg,png,pdf"`) | 단순하고 조회 빠름. 게시판 설정은 쓰기 빈도 낮음 | 별도 테이블(과도한 정규화), JSON 배열(PostgreSQL JSONB 가능하나 단순 CSV 충분) |

---

## 의존 기능

- 선행: SFR-100 (기반 구축) ✅, SFR-108 (OAuth 인증) 🔲
- 후행: SFR-101 (게시판 CRUD) — `board_id` FK 필요

---

## 미결/리스크

- [ ] Phase 1은 관리자 UI 없음 → 게시판 초기 데이터는 Alembic seed migration으로 삽입 (방식 확정 필요)
- [ ] `board_code` 변경 시 클라이언트 URL 호환성 처리 (Phase 1은 변경 금지 정책으로 단순화)
- [ ] `secret_yn`, `like_yn`는 Phase 1 API에서 요청/응답에 포함하지 않음 (고정 false)
- [ ] `auto_reply_enabled=true` 설정 시 SFR-104 미구현 상태면 동작 안 함 (플래그만 저장, 실행은 SFR-104 이후)

---

## 테스트 기준

**정상:**
- ADMIN이 게시판 생성 → `BRD_XXXXXXXX` ID 발급, `board_code` UNIQUE 저장 확인
- 게시판 목록 조회 → `use_yn=true`, `del_yn=false` 필터, `sort_order` ASC 정렬 확인
- 게시판 수정 → 변경된 필드만 반영, `updated_at` 갱신 확인
- 게시글 없는 게시판 삭제 → `del_yn=true`, 목록 조회에서 미노출 확인
- GUEST가 게시판 목록/단건 조회 → 200 정상 응답

**예외:**
- 비로그인/USER 권한으로 게시판 생성/수정/삭제 → 403
- 중복 `board_code`로 생성 → 409 `BOARD_CODE_ALREADY_EXISTS`
- 존재하지 않는 `board_id`로 수정/삭제 → 404 `BOARD_NOT_FOUND`
- 게시글이 있는 게시판 삭제 → 409 `BOARD_HAS_POSTS`
- `del_yn=true` 게시판 조회 → 404

---

## 참고

- [SRS_P1 §3.3 ID 채번 전략](../specs/srs/SRS_P1.md)
- [05_ERD §3.4 Board 도메인](../specs/05_ERD.md)
- [SFR-108 OAuth 인증](./SFR-108_OAuth인증.md)
- [SFR-101 게시판 CRUD](./SFR-101_게시판CRUD.md)
