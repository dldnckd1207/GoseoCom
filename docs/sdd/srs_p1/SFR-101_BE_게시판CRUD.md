---
tags: [spec]
cssclasses:
  - my_style_width_100
status: active
created: 2026-04-27 00:00
updated: 2026-04-28 00:00
parent: "[[SRS_P1]]"
domain: "[[04_Domain]]"
requirement: "SFR-101"
---

# SFR-101 — 게시판 CRUD (게시글 / 댓글)

> [!note] 이 문서는 왜 작성하는가
> 하나의 기능을 어떻게 설계하고 구현할지 정리하는 문서.
> "결정 사항" 테이블에 왜 이 방식을 선택했는지 기록하는 것이 핵심이다.

---

## 배경

SFR-105(게시판 관리)로 게시판 엔티티가 구성되었다.
SFR-101은 해당 게시판 위에서 동작하는 **게시글 / 댓글 CRUD**를 구현한다.

- 게시글 읽기(목록·단건)는 GUEST 허용 — 단, 게시판의 `read_yn` / `guest_read_yn` 설정을 따른다.
- 게시글 / 댓글 작성·수정·삭제는 USER 이상 — 게시판의 `write_yn`, `comment_yn` 설정을 따른다.
- 수정·삭제는 **본인 또는 ADMIN 이상**만 가능하다 (BBR-05).
- 파일 첨부는 게시판 정책(`attach_yn`, `attach_ext`, `attach_size`, `attach_count`)에 따라 검증한다.
- Phase 1에서는 좋아요, 비밀글, AI 자동 답변 실행은 제외한다.

---

## 기능 설명

### 게시글 (Post)
- `POST_` ID-Gen으로 게시글을 식별한다.
- 게시글 작성 시 `board_code`로 게시판을 조회하고, 게시판 설정(`write_yn`, `attach_yn` 등)을 검증한다.
- 단건 조회 시 `view_count`를 원자적으로 +1 한다.
- 수정·삭제 시 `cms_th_post_history`에 이력을 append한다 (수정 전 내용 보존).
- 공지(`notice_yn=true`) 설정은 ADMIN 이상만 허용하며, 게시판 `board.notice_yn=true` 필요.
- 답글(`parent_id` 지정)은 게시판 `reply_yn=true`이고 `parent.depth=0`일 때만 허용 (depth=1 제한).
- 파일 첨부: 작성/수정 시 `file_ids` 수신 → `file_map` 연결. 게시판 정책 검증 후 `core/files` 서비스 호출.

### 댓글 (Comment)
- `CMT_` ID-Gen으로 댓글을 식별한다.
- 댓글 작성 시 게시판 `comment_yn=true` 여부를 검증한다.
- 댓글 작성 / Soft Delete 시 `cms_tn_post.comment_count`를 연동한다.
- `is_filtered`, `filter_reason` 필드는 Phase 3 선반영 — Phase 1에서는 항상 `false`.

---

## 핵심 흐름

### 게시글 목록 조회 (GUEST — `/api/v1/`)

```
1. 클라이언트 → POST /api/v1/posts/list (body: board_code, keyword, page, size)
2. 서버 → board_code로 게시판 조회 (use_yn=true, del_yn=false)
   없으면 → 404 BOARD_NOT_FOUND
3. 토큰 확인 (Optional)
   - 비회원: guest_read_yn=false → 403 BOARD_READ_FORBIDDEN
   - 로그인: read_yn=false → 403 BOARD_READ_FORBIDDEN
4. 서버 → del_yn=false 게시글, notice_yn=true 우선 → created_at DESC 페이지네이션
5. 서버 → 경량 게시글 목록 반환 (200 SUCCESS)
```

### 게시글 단건 조회 (GUEST — `/api/v1/`)

```
1. 클라이언트 → GET /api/v1/posts/{post_id}
2. 서버 → post 존재 확인 (del_yn=false)
   없으면 → 404 POST_NOT_FOUND
3. 서버 → post.board_id로 board 조회
4. 토큰 확인 (Optional)
   - 비회원: guest_read_yn=false → 403 BOARD_READ_FORBIDDEN
   - 로그인: read_yn=false → 403 BOARD_READ_FORBIDDEN
5. 서버 → view_count +1 (atomic UPDATE)
6. 서버 → 전체 필드 post + 첨부파일 목록 반환 (200 SUCCESS)
```

### 게시글 작성 (USER — `/api/v1/`)

```
1. USER → POST /api/v1/posts (body: board_code, title, content, ...)
2. 서버 → board_code로 게시판 조회
   없으면 → 404 BOARD_NOT_FOUND
3. 서버 → 쓰기 권한 확인
   - write_yn=false → 403 BOARD_WRITE_FORBIDDEN
4. 서버 → notice_yn=true 요청 시
   - board.notice_yn=false → 403 FORBIDDEN (공지 기능 비활성 게시판)
   - USER 권한 → 403 FORBIDDEN (ADMIN만 공지 설정 가능)
5. 서버 → parent_id 지정 시
   - reply_yn=false → 403 REPLY_NOT_ALLOWED
   - parent post 존재 확인 (같은 board_id, del_yn=false)
   - parent.depth != 0 → 403 REPLY_NOT_ALLOWED (depth=1 제한)
6. 서버 → file_ids 전달 시 파일 검증
   - dict.fromkeys(file_ids)로 중복 제거 (순서 보존)
   - 각 file_id: com_tn_file 존재·del_yn=false 확인 → FILE_NOT_FOUND
   - 각 file_id: file.created_by == payload["sub"] 또는 ADMIN → FILE_ACCESS_FORBIDDEN
   - attach_yn=false → ATTACH_NOT_ALLOWED
   - attach_count 초과 → ATTACH_COUNT_EXCEEDED
   - attach_size 초과 파일 존재 → ATTACH_SIZE_EXCEEDED
   - attach_ext 불일치 파일 존재 → ATTACH_EXT_NOT_ALLOWED
     (Phase 1: `file_ext` 컬럼 기준 검증. `mime_type`과 교차 검증은 Phase 2 이후)
7. 서버 → author_name = payload["name"] (JWT 클레임에서 직접 추출)
8. 서버 → cms_tn_post INSERT (ID-Gen: POST_XXXXXXXX)
9. 서버 → file_ids → file_map INSERT (target_type=POST, target_id=post.id)
10. 서버 → 작성된 post 반환 (201 CREATED)
```

### 게시글 수정 (USER — `/api/v1/`)

```
1. USER → PUT /api/v1/posts/{post_id}
2. 서버 → post 존재 확인 (del_yn=false)
   없으면 → 404 POST_NOT_FOUND
3. 서버 → post.board_id로 board 조회
4. 서버 → 본인(user_id) 또는 ADMIN 이상 확인
   아니면 → 403 FORBIDDEN
5. 서버 → notice_yn=true 요청 시
   - board.notice_yn=false → 403 FORBIDDEN (공지 기능 비활성 게시판)
   - USER 권한 → 403 FORBIDDEN (ADMIN만 공지 설정 가능)
6. 서버 → file_ids 전달 시 파일 사전 검증 (작성 흐름과 동일)
   - dict.fromkeys(file_ids)로 중복 제거
   - 각 file_id: com_tn_file 존재·del_yn=false 확인 → FILE_NOT_FOUND
   - 각 file_id: file.created_by == payload["sub"] 또는 ADMIN → FILE_ACCESS_FORBIDDEN
   - attach_yn=false → ATTACH_NOT_ALLOWED
   - attach_count 초과 → ATTACH_COUNT_EXCEEDED
   - attach_size 초과 → ATTACH_SIZE_EXCEEDED
   - attach_ext 불일치 → ATTACH_EXT_NOT_ALLOWED (Phase 1: file_ext 기준)
7. 서버 → [트랜잭션 시작]
   - cms_th_post_history INSERT (action=UPDATE, 수정 전 title·content)
   - cms_tn_post UPDATE
   - file_ids 전달 시: 기존 file_map (target_type=POST, target_id=post_id) → del_yn=true Soft Delete
   - 새 file_ids 각각: file_map upsert (기존 row del_yn=false 복원 또는 신규 INSERT)
   - 실패 시 전체 롤백
8. 서버 → 수정된 post 반환 (200 UPDATED)
```

### 게시글 삭제 (USER — `/api/v1/`)

```
1. USER → DELETE /api/v1/posts/{post_id}
2. 서버 → post 존재 확인 (del_yn=false)
3. 없으면 → 404 POST_NOT_FOUND
4. 서버 → 본인(user_id) 또는 ADMIN 이상 확인
5. 아니면 → 403 FORBIDDEN
6. 서버 → cms_th_post_history INSERT (action=DELETE)
7. 서버 → cms_tn_post Soft Delete (del_yn=true)
8. 서버 → 200 DELETED
```

### 댓글 목록 조회 (GUEST — `/api/v1/`)

```
1. 클라이언트 → POST /api/v1/posts/{post_id}/comments/list
2. 서버 → post 존재 확인 (del_yn=false)
   없으면 → 404 POST_NOT_FOUND
3. 서버 → post.board_id로 board 조회
4. 토큰 확인 (Optional)
   - 비회원: guest_read_yn=false → 403 BOARD_READ_FORBIDDEN
   - 로그인: read_yn=false → 403 BOARD_READ_FORBIDDEN
5. 서버 → root 댓글 조회 (parent_id=null, del_yn 무관) → created_at ASC 페이지네이션
   (total = del_yn 무관 root 전체 수. 구현 단순화 — replies 유무 사전 조회 불필요)
6. 서버 → 해당 페이지 root id 목록으로 replies (depth=1, del_yn=false) IN 쿼리 별도 조회
7. 서버 → del_yn=true root는 content="삭제된 댓글입니다.", author_name=null, is_deleted=true로 변환
8. 서버 → root 댓글 각각에 replies 배열 조립 후 반환 (200 SUCCESS)
```

### 댓글 작성 (USER — `/api/v1/`)

```
1. USER → POST /api/v1/posts/{post_id}/comments
2. 서버 → post 존재 확인 (del_yn=false)
   없으면 → 404 POST_NOT_FOUND
3. 서버 → post.board_id로 board 조회 (use_yn=true, del_yn=false 확인)
   board 비활성이면 → 404 BOARD_NOT_FOUND
4. 서버 → board.comment_yn=false → 403 COMMENT_NOT_ALLOWED
5. 서버 → parent_id 지정 시
   - parent comment 존재 확인 (같은 post_id, del_yn=false)
   - parent.depth != 0 → 403 REPLY_NOT_ALLOWED (depth=1 제한)
6. 서버 → author_name = payload["name"] (JWT 클레임에서 직접 추출)
7. 서버 → cms_tn_comment INSERT (depth = parent_id 있으면 1, 없으면 0)
8. 서버 → cms_tn_post.comment_count +1 (atomic UPDATE)
9. 서버 → 작성된 comment 반환 (201 CREATED)
```

### 댓글 수정 / 삭제 (USER — `/api/v1/`)

```
수정:
1. USER → PUT /api/v1/posts/{post_id}/comments/{comment_id}
2. 서버 → (comment_id, post_id) 조건으로 comment 조회 (del_yn=false)
   없으면 → 404 COMMENT_NOT_FOUND  (post_id 불일치도 동일 처리)
3. 서버 → 본인(user_id) 또는 ADMIN 이상 확인
   아니면 → 403 FORBIDDEN
4. 서버 → cms_tn_comment UPDATE
5. 서버 → 수정된 comment 반환 (200 UPDATED)

삭제:
1. USER → DELETE /api/v1/posts/{post_id}/comments/{comment_id}
2. 서버 → (comment_id, post_id) 조건으로 comment 조회 (del_yn=false)
   없으면 → 404 COMMENT_NOT_FOUND  (post_id 불일치도 동일 처리)
3. 서버 → 본인(user_id) 또는 ADMIN 이상 확인
   아니면 → 403 FORBIDDEN
4. 서버 → cms_tn_comment Soft Delete (del_yn=true, content 유지)
5. 서버 → root 댓글인 경우 (depth=0): comment_count -1 (대댓글은 유지, placeholder로 노출)
   대댓글인 경우 (depth=1): comment_count -1
6. 서버 → 200 DELETED
```

---

## 설계

### 구조

- **영향 받는 레이어**: Router → Service → Repository
- **신규 생성**:
  - `app/board/post_schemas.py` — Post Request/Response
  - `app/board/comment_schemas.py` — Comment Request/Response
  - `app/board/post_repository.py` — Post DB 쿼리
  - `app/board/comment_repository.py` — Comment DB 쿼리
  - `app/board/post_service.py` — Post 비즈니스 로직
  - `app/board/comment_service.py` — Comment 비즈니스 로직
  - `app/board/post_router.py` — 게시글 API (`/api/v1/posts/`)
  - `app/board/comment_router.py` — 댓글 API (`/api/v1/posts/{post_id}/comments/`)
- **변경 대상**:
  - `app/main.py` — post_router, comment_router 등록
  - `app/core/security.py` — `create_access_token()`에 `name: str` 파라미터 추가
  - `app/auth/service.py` — `create_access_token()` 호출 시 `user.name` 전달
  - `app/auth/dev_router.py` — dev token 발급 시 `user.name` 전달
- **의존성**: SFR-105 (`Board` 모델), SFR-108 (`require_level`)

> **JWT payload 변경:** `author_name` 스냅샷을 DB 조회 없이 처리하기 위해 Access Token에 `name` 클레임 추가.
> 게시글/댓글 작성 시 `payload["name"]`으로 바로 사용.
> ```python
> # 변경 전
> {"sub": user_id, "level": user_level, "blocked": blocked, ...}
> # 변경 후
> {"sub": user_id, "level": user_level, "name": user_name, "blocked": blocked, ...}
> ```

### 데이터

#### cms_tn_post (기존 — 변경 없음)

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | VARCHAR(20) PK | ID-Gen (`POST_`) |
| board_id | VARCHAR(20) FK | → cms_tn_board.id |
| category_id | VARCHAR(20) FK NULL | → cms_tn_board_category.id (Phase 3) |
| user_id | VARCHAR(20) FK | → com_tn_user.id |
| author_name | VARCHAR(100) | 작성 시 user.name 스냅샷 |
| parent_id | VARCHAR(20) FK NULL | 답글 대상 post.id |
| depth | INT | 0=원글, 1=답글 |
| title | VARCHAR(255) | |
| content | TEXT | |
| notice_yn | BOOLEAN | 공지 여부 (ADMIN만 true 설정) |
| secret_yn | BOOLEAN | 비밀글 (Phase 3 — 항상 false) |
| view_count | INT | 조회수 (atomic UPDATE) |
| like_count | INT | 좋아요 (Phase 3 — 항상 0) |
| comment_count | INT | 삭제되지 않은 전체 댓글+대댓글 수. 댓글 목록 `total`(root 페이지네이션 기준)과 의도적으로 다를 수 있음 |
| auto_reply_status | VARCHAR(20) | PENDING 고정 (SFR-104 미구현) |
| auto_reply_at | TIMESTAMPTZ NULL | |
| TimestampMixin | — | created_at, created_by, updated_at, updated_by |
| SoftDeleteMixin | — | del_yn, deleted_at, deleted_by |

#### cms_th_post_history (기존 — 변경 없음, append-only)

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | BIGSERIAL PK | |
| post_id | VARCHAR(20) FK | |
| version | INT | 게시글별 단조 증가 — `COALESCE(MAX(version), 0) + 1` 같은 트랜잭션 내 SELECT 후 INSERT |
| action | VARCHAR(20) | `CREATE` \| `UPDATE` \| `DELETE` |
| title | VARCHAR(255) | 변경 전 제목 |
| content | TEXT | 변경 전 본문 |
| changed_by | VARCHAR(20) FK | 변경 주체 user_id |
| changed_at | TIMESTAMPTZ | |

#### cms_tn_comment (기존 — 변경 없음)

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | VARCHAR(20) PK | ID-Gen (`CMT_`) |
| post_id | VARCHAR(20) FK | → cms_tn_post.id |
| user_id | VARCHAR(20) FK | → com_tn_user.id |
| author_name | VARCHAR(100) | 작성 시 user.name 스냅샷 |
| parent_id | VARCHAR(20) FK NULL | 대댓글 대상 comment.id |
| depth | INT | 0=댓글, 1=대댓글 |
| content | TEXT | |
| like_count | INT | Phase 3 — 항상 0 |
| is_filtered | BOOLEAN | Phase 3 — 항상 false |
| filter_reason | VARCHAR(255) NULL | Phase 3 |
| filtered_at | TIMESTAMPTZ NULL | Phase 3 |
| filter_reviewed_by | VARCHAR(20) FK NULL | Phase 3 |
| TimestampMixin + SoftDeleteMixin | — | |

### 인터페이스

#### 게시글 API (`/api/v1/posts/`)

| Method | Path | 인증 | 설명 |
|--------|------|------|------|
| POST | `/api/v1/posts/list` | GUEST (Optional) | 게시글 목록 (board_code 필수) |
| GET | `/api/v1/posts/{post_id}` | GUEST (Optional) | 게시글 단건 + view_count++ + files |
| POST | `/api/v1/posts` | USER | 게시글 작성 (file_ids 선택) |
| PUT | `/api/v1/posts/{post_id}` | USER | 게시글 수정 (본인 or ADMIN, file_ids 선택) |
| DELETE | `/api/v1/posts/{post_id}` | USER | 게시글 삭제 (본인 or ADMIN) |
| POST | `/api/v1/boards/{board_code}/uploads` | USER | 게시판 파일 업로드 (첨부 정책 검증) |

#### 댓글 API (`/api/v1/posts/{post_id}/comments/`)

| Method | Path | 인증 | 설명 |
|--------|------|------|------|
| POST | `/api/v1/posts/{post_id}/comments/list` | GUEST (Optional) | 댓글 목록 |
| POST | `/api/v1/posts/{post_id}/comments` | USER | 댓글 작성 |
| PUT | `/api/v1/posts/{post_id}/comments/{comment_id}` | USER | 댓글 수정 (본인 or ADMIN) |
| DELETE | `/api/v1/posts/{post_id}/comments/{comment_id}` | USER | 댓글 삭제 (본인 or ADMIN) |

#### 요청 스키마

`POST /api/v1/posts/list` 요청:
```json
{
  "board_code": "translation",
  "keyword": null,
  "page": 1,
  "size": 20
}
```

`POST /api/v1/posts` 요청:
```json
{
  "board_code": "translation",
  "title": "제목",
  "content": "본문 내용",
  "notice_yn": false,
  "parent_id": null,
  "file_ids": ["FILE_00000001", "FILE_00000002"]
}
```

> `file_ids`: 선업로드 API로 발급된 FILE ID 목록. 빈 배열 또는 생략 시 첨부 없음. 중복 값은 서버에서 순서 보존 중복 제거(`dict.fromkeys`) 후 처리.

`PUT /api/v1/posts/{post_id}` 요청 (변경 필드만):
```json
{
  "title": "수정된 제목",
  "content": "수정된 본문",
  "file_ids": ["FILE_00000001", "FILE_00000003"]
}
```

> `file_ids`: 수정 후 최종 첨부 목록 (전체 교체).
> 기존 `file_map` Soft Delete → 새 목록으로 재구성.
> `com_tn_file.del_yn=true`인 파일은 사용 불가 (`FILE_NOT_FOUND` 반환).
> `file_map.del_yn=true` row만 upsert로 복원.

`POST /api/v1/posts/{post_id}/comments` 요청:
```json
{
  "content": "댓글 내용",
  "parent_id": null
}
```

#### 응답 스키마

`POST /api/v1/posts/list` 응답 (경량):
```json
{
  "header": { "success": true, "code": "SUCCESS", "message": "요청이 성공적으로 처리되었습니다." },
  "body": {
    "data": {
      "items": [
        {
          "id": "POST_00000001",
          "board_id": "BRD_00000001",
          "board_code": "translation",
          "author_name": "홍길동",
          "is_ai_gen": false,
          "title": "제목",
          "notice_yn": false,
          "view_count": 10,
          "comment_count": 3,
          "created_at": "2026-04-27T00:00:00Z"
        }
      ],
      "total": 1,
      "page": 1,
      "size": 20
    }
  }
}
```

`GET /api/v1/posts/{post_id}` 응답 (전체):
```json
{
  "header": { "success": true, "code": "SUCCESS", "message": "요청이 성공적으로 처리되었습니다." },
  "body": {
    "data": {
      "id": "POST_00000001",
      "board_id": "BRD_00000001",
      "board_code": "translation",
      "user_id": "USR_00000001",
      "author_name": "홍길동",
      "is_ai_gen": false,
      "parent_id": null,
      "depth": 0,
      "title": "제목",
      "content": "본문 내용",
      "notice_yn": false,
      "view_count": 11,
      "comment_count": 3,
      "auto_reply_status": "PENDING",
      "files": [
        {
          "file_id": "FILE_00000001",
          "original_name": "첨부파일.pdf",
          "url_path": "/files/uuid-here",
          "file_size": 204800,
          "file_ext": "pdf"
        }
      ],
      "created_at": "2026-04-27T00:00:00Z",
      "updated_at": "2026-04-27T00:00:00Z"
    }
  }
}
```

`POST /api/v1/posts/{post_id}/comments/list` 응답 (Nested — root 댓글 기준 페이지네이션):
```json
{
  "header": { "success": true, "code": "SUCCESS", "message": "요청이 성공적으로 처리되었습니다." },
  "body": {
    "data": {
      "items": [
        {
          "id": "CMT_00000001",
          "post_id": "POST_00000001",
          "user_id": "USR_00000001",
          "author_name": "홍길동",
          "is_ai_gen": false,
          "is_deleted": false,
          "parent_id": null,
          "depth": 0,
          "content": "댓글 내용",
          "created_at": "2026-04-27T00:00:00Z",
          "updated_at": "2026-04-27T00:00:00Z",
          "replies": [
            {
              "id": "CMT_00000002",
              "post_id": "POST_00000001",
              "user_id": "USR_00000002",
              "author_name": "김철수",
              "is_ai_gen": false,
              "is_deleted": false,
              "parent_id": "CMT_00000001",
              "depth": 1,
              "content": "대댓글 내용",
              "created_at": "2026-04-27T00:01:00Z",
              "updated_at": "2026-04-27T00:01:00Z",
              "replies": []
            }
          ]
        },
        {
          "id": "CMT_00000003",
          "post_id": "POST_00000001",
          "user_id": null,
          "author_name": null,
          "is_ai_gen": false,
          "is_deleted": true,
          "parent_id": null,
          "depth": 0,
          "content": "삭제된 댓글입니다.",
          "created_at": "2026-04-27T00:02:00Z",
          "updated_at": "2026-04-27T00:05:00Z",
          "replies": []
        }
      ],
      "total": 2,
      "page": 1,
      "size": 20
    }
  }
}
```

> `total`: root 댓글 전체 수 (del_yn 무관). page/size는 이 집합 기준으로 계산.
> replies: root 페이지네이션 이후 해당 root id 목록으로 별도 IN 쿼리 조회 (del_yn=false만).
> `post.comment_count`는 삭제되지 않은 전체 댓글+대댓글 수이며, `total`(root 페이지네이션 기준)과 의도적으로 다를 수 있다.

#### 에러 응답

| 상황 | HTTP | code |
|------|------|------|
| 게시판 없음 / 비활성 | 404 | `BOARD_NOT_FOUND` |
| 게시글 없음 | 404 | `POST_NOT_FOUND` |
| 댓글 없음 / post_id 불일치 | 404 | `COMMENT_NOT_FOUND` |
| 비회원이 `guest_read_yn=false` 게시판 접근 | 403 | `BOARD_READ_FORBIDDEN` |
| 로그인 사용자가 `read_yn=false` 게시판 접근 | 403 | `BOARD_READ_FORBIDDEN` |
| `write_yn=false` 게시판에 게시글 작성 | 403 | `BOARD_WRITE_FORBIDDEN` |
| `comment_yn=false` 게시판에 댓글 작성 | 403 | `COMMENT_NOT_ALLOWED` |
| `reply_yn=false` 게시판에 답글 / depth 초과 | 403 | `REPLY_NOT_ALLOWED` |
| USER가 `notice_yn=true` 설정 / `board.notice_yn=false` | 403 | `FORBIDDEN` |
| 본인 소유 아닌 게시글/댓글 수정·삭제 | 403 | `FORBIDDEN` |
| 파일 없음 또는 삭제된 파일 첨부 시도 | 404 | `FILE_NOT_FOUND` |
| 타인 파일 첨부 시도 | 403 | `FILE_ACCESS_FORBIDDEN` |
| `attach_yn=false` 게시판에 파일 첨부 시도 | 403 | `ATTACH_NOT_ALLOWED` |
| 첨부 개수 초과 | 400 | `ATTACH_COUNT_EXCEEDED` |
| 첨부 크기 초과 | 400 | `ATTACH_SIZE_EXCEEDED` |
| 허용되지 않은 첨부 확장자 | 400 | `ATTACH_EXT_NOT_ALLOWED` |

---

## 결정 사항

| 주제 | 선택 | 이유 | 검토한 대안 |
|------|------|------|------------|
| Post URL | `/api/v1/posts/...` (board_code는 body) | post_id만으로 게시글 식별 가능, URL 단순화 | `/boards/{code}/posts/...` (게시판 중첩 URL, 단건 조회 시도 불필요) |
| view_count 증가 | atomic `UPDATE post SET view_count = view_count + 1` | SELECT + UPDATE 분리 시 race condition 발생 가능 | Redis counter (Phase 2 이후) |
| comment_count 연동 | 댓글 작성/삭제 시 atomic UPDATE | 항상 정확한 카운트 유지 | 매번 COUNT 쿼리 (성능 저하) |
| author_name 스냅샷 | JWT `name` 클레임에서 추출 (`payload["name"]`) | DB 추가 조회 없음. Stateless JWT에서 기본 사용자 정보는 JWT에 포함하는 것이 원칙 | DB 조회(매 요청마다 쿼리 추가), FK join(이름 변경 시 표시 달라짐) |
| PostHistory | 수정·삭제 시만 INSERT (CREATE 제외) | History는 "변경 이력" 목적 — 최초 원문은 post 테이블 자체가 보존. 수정 시 "수정 전 내용" 기록으로 원문 복구 가능 | CREATE도 INSERT (과도한 기록) |
| is_ai_gen 파생 필드 | `user_id == 'USR_00000000'` 비교 (`USR_00000000` 고정 — `USER_00000000` 아님) | DB 컬럼 추가 없이 AI 생성 판별 | `author_type` 컬럼 (SRS §3.6 결정) |
| 파일 첨부 | Phase 1 포함 — 선업로드 후 `file_ids` 전달, `file_map` 연결 | PRD/SRS Must 범위. 게시판·번역기 공통 파일 인프라 재사용 | Phase 1 제외(SRS와 불일치), SFR-102 별도(SFR-102는 OCR로 흡수됨) |
| 파일 수정 정책 | file_map 전체 교체 — 기존 file_map Soft Delete 후 새 file_ids로 재구성. `file_map.del_yn=true` row는 upsert 복원. `com_tn_file.del_yn=true` 파일은 사용 불가 | 삭제된 파일 재노출 방지. 파일 엔티티와 매핑을 분리해서 관리 | add/remove 분리(구현 복잡도 증가), com_tn_file 복원(삭제 파일 재노출 위험) |
| 좋아요·비밀글 | Phase 3 — API 미노출, 컬럼만 선반영 | 마이그레이션 비용 최소화 | Phase 3 때 컬럼 추가 (마이그레이션 추가 필요) |
| 게시글 목록 board_code 포함 | 목록 응답에 `board_code` 추가 | 목록 조회 시 board를 이미 조회하므로 추가 비용 없음. 프론트에서 URL 구성 시 필요 | board_id만 유지(프론트 캐시 의존) |
| 댓글 응답 구조 | Nested B — root 댓글에 replies 배열 포함 | 프론트 트리 조립 불필요, depth=1 제한 시 쿼리 2번으로 처리 가능 | Flat 방식(프론트 조립), 별도 API(UX 복잡) |
| 댓글 depth 제한 | depth=1 고정 (대댓글 1단계) | 페이지네이션·쿼리 단순화. Phase 3에서 N단계 확장 | N단계 무제한(WITH RECURSIVE CTE, 페이지네이션 복잡) |
| root 댓글 삭제 | placeholder 방식 — `del_yn=true` root는 replies 유무 관계없이 목록에 포함. `is_deleted=true`, content="삭제된 댓글입니다.", author_name=null | 구현 단순 (replies 사전 조회 불필요). 대댓글 문맥 보존 | cascade soft delete, 삭제 제한, replies 있을 때만 placeholder(사전 조회 필요) |
| file_ids 중복 제거 | `dict.fromkeys(file_ids)`로 서버에서 자동 중복 제거 (순서 보존) | 클라이언트 실수 관대 처리. attach_count 계산 일관성 확보 | 400 DUPLICATE_FILE_ID 거부(클라이언트 부담) |

---

## 의존 기능

- 선행: SFR-100 (기반 구축) ✅, SFR-108 (OAuth 인증) 🔲, SFR-105 (게시판 관리) ✅
- 후행: SFR-104 (AI 자동 답변) — `auto_reply_status` FK

---

## 미결 / 리스크

- [ ] `view_count` 중복 증가 방지 (같은 사용자 반복 조회) — Phase 1은 단순 +1, Phase 2에서 Redis 세션 기반 중복 제거
- [x] 댓글 중첩 구조 — **depth=1 고정** (댓글 + 대댓글 1단계). Phase 3에서 N단계 확장 검토
- [x] `guest_write_yn` Phase 1 처리 — 기본값 `false`, `require_level(USER)` 적용으로 비회원 접근 자체 차단. 별도 서버 체크 불필요. Phase 3에서 GUEST 작성 허용 게시판 지원 시 활성화
- [x] 파일 첨부 — Phase 1 포함. 선업로드 + `file_map` 전체 교체. 소유권 검증 + `dict.fromkeys` 중복 제거
- [x] root 댓글 삭제 정책 — placeholder 방식 (B). 대댓글 유지, `is_deleted=true` 필드로 구분
- [x] `read_yn` 체크 — 목록/단건/댓글 목록 흐름 전부에 로그인/비회원 분기 추가
- [x] ADMIN 권한 — Phase 1 활성화. `SRS_P1 §3.2` 수정 완료 (Admin UI만 Phase 3)
- [x] PostHistory — Phase 1부터 수정·삭제 시 INSERT (CREATE 제외)
- [x] 댓글 소속 검증 — `(comment_id, post_id)` 조건 조회로 URL 불일치 방어
- [x] 답글/대댓글 depth 검증 — parent 존재, 같은 board_id/post_id, depth=0 확인
- [x] `AI 시드 계정 ID` — `USR_00000000` 표기 확정 (결정 사항에 명시)
- [ ] 게시글 삭제 시 연결된 댓글 처리 — Soft Delete만, 댓글 데이터는 유지 (조회 API에서 del_yn=false 필터로 미노출)

---

## 테스트 기준

**정상:**
- 게시글 목록 조회 → notice_yn=true 우선 + created_at DESC 정렬, board_code 포함
- 게시글 단건 조회 → view_count +1, board read_yn/guest_read_yn 확인, files[] 포함
- USER가 게시글 작성 → `POST_XXXXXXXX` ID 발급, author_name 스냅샷
- 게시글 수정 → PostHistory INSERT (수정 전 내용), updated_at 갱신
- 게시글 삭제 → del_yn=true, 목록 미노출, PostHistory INSERT
- USER가 댓글 작성 → comment_count +1, replies 배열 포함 응답
- 대댓글 작성 → depth=1, root 댓글 replies에 포함
- USER가 댓글 삭제 → comment_count -1
- 파일 업로드 → FILE_XXXXXXXX 발급
- 게시글 작성 시 file_ids 전달 → file_map 생성, 단건 응답에 files[] 포함
- 게시글 수정 시 file_ids 교체 → 기존 file_map Soft Delete, 새 file_map 생성

**예외:**
- 비회원이 guest_read_yn=false 게시판 조회 → 403 BOARD_READ_FORBIDDEN
- 로그인 사용자가 read_yn=false 게시판 조회 → 403 BOARD_READ_FORBIDDEN
- write_yn=false 게시판에 게시글 작성 → 403 BOARD_WRITE_FORBIDDEN
- reply_yn=false 게시판에 답글 작성 → 403 REPLY_NOT_ALLOWED
- depth=1 댓글에 대댓글 작성 시도 → 403 REPLY_NOT_ALLOWED
- comment_yn=false 게시판에 댓글 작성 → 403 COMMENT_NOT_ALLOWED
- USER가 notice_yn=true 설정 → 403 FORBIDDEN
- 타인의 게시글 수정·삭제 → 403 FORBIDDEN
- 없는 post_id 조회 → 404 POST_NOT_FOUND
- 없는 comment_id 수정·삭제 → 404 COMMENT_NOT_FOUND
- attach_yn=false 게시판에 file_ids 전달 → 403 ATTACH_NOT_ALLOWED
- 타인 파일 ID 첨부 시도 (작성·수정) → 403 FILE_ACCESS_FORBIDDEN
- 삭제된 파일(del_yn=true) 첨부 시도 (작성·수정) → 404 FILE_NOT_FOUND
- 첨부 개수/크기/확장자 위반 → 400 ATTACH_COUNT/SIZE/EXT_EXCEEDED
- 게시글 수정 시 파일 검증 실패 → 기존 첨부 유지 (트랜잭션 롤백)
- root 댓글 삭제 후 목록 조회 → placeholder 표시, 대댓글 유지, comment_count -1

---

## 참고

- [SRS_P1 §3.2 인증/권한](../specs/srs/SRS_P1.md)
- [SRS_P1 §3.4 파일 업로드/서빙](../specs/srs/SRS_P1.md)
- [SRS_P1 §3.6 AI 에이전트](../specs/srs/SRS_P1.md)
- [05_ERD §3.4 Board 도메인](../specs/05_ERD.md)
- [SFR-105 게시판 관리](./SFR-105_BE_다중게시판.md)
- [SFR-108 OAuth 인증](./SFR-108_BE_OAuth인증.md)
- SFR-104 AI 자동 답변 (작성 예정)
