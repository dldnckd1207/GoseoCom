# Plan: 게시판 카테고리 API 구현 (sfr-108-board-category)

**작성자**: cellmin  
**날짜**: 2026-05-16  
**관련 이슈**: Redmine #108

---

## 1. 배경 및 목표

`BoardCategory` 모델과 `Post.category_id` FK는 Phase 3으로 선반영됨.  
커뮤니티 글 작성 화면(#100) 목업의 "시대" 드롭다운(선사/삼국/고려/조선) 구현에 필요.  
BE API 구현 + FE 연동까지 한 번에 완료.

---

## 2. 현황

| 항목 | 상태 |
|------|------|
| `BoardCategory` 모델 | ✅ 선반영 (`cms_tn_board_category`) |
| `Post.category_id` FK | ✅ nullable |
| 커뮤니티 게시판 `category_yn` | ❌ `false` |
| 카테고리 시드 | ❌ 없음 |
| 카테고리 목록 API | ❌ 없음 |
| `PostCreateRequest.category_id` | ❌ 없음 |
| FE "시대" 드롭다운 | ❌ 없음 |

---

## 3. 요구사항

### BE (apps/server)

| # | 항목 | 설명 |
|---|------|------|
| B-1 | 마이그레이션: `category_yn` 활성화 | 커뮤니티 3개 게시판(translation, questions, free) `category_yn=true` |
| B-2 | 마이그레이션: 카테고리 시드 | 각 게시판에 선사/삼국/고려/조선 4개 카테고리 생성 (총 12개) |
| B-3 | 카테고리 목록 API | `GET /api/v1/boards/{board_code}/categories` → 해당 게시판의 활성 카테고리 목록 반환 |
| B-4 | 글 작성 API 확장 | `PostCreateRequest`에 `category_id: str | None` 추가 (optional) |
| B-5 | `category_id` 검증 | 지정 시 ① 존재 여부 ② 작성 게시판 소속(`board_id` 일치) ③ `use_yn=true`, `del_yn=false` ④ `board.category_yn=true` 확인. 위반 시 400 반환 |

### FE (apps/client)

| # | 항목 | 설명 |
|---|------|------|
| F-1 | 엔드포인트 추가 | `BOARD_CATEGORIES: (boardCode) => /api/v1/boards/{boardCode}/categories` |
| F-2 | 타입 추가 | `BoardCategoryItem` 타입 |
| F-3 | write loader 확장 | 각 board의 카테고리 목록 병렬 조회 → `categories` 반환 |
| F-4 | "시대" 드롭다운 UI | 선택된 글 유형(board_code)에 해당하는 카테고리 표시, 선택 시 `category_id` 전송 |
| F-5 | action `category_id` 전송 | action에서 `formData.get('category_id')` 읽어 POST body에 포함. 미선택(`''`)은 `null`로 변환 |

### 비기능 요구사항

| # | 항목 |
|---|------|
| N-1 | lint(ruff) + mypy (BE) 통과 |
| N-2 | `npm run lint` + `npm run typecheck` (FE) 통과 |
| N-3 | 카테고리 미선택 허용 (optional) |
| N-4 | boards가 없으면 카테고리 조회 없이 빈 배열 반환 |
| N-5 | 카테고리 API 일부 실패 시 해당 board만 빈 배열, 글쓰기 화면 유지 |

---

## 4. API 설계

### `GET /api/v1/boards/{board_code}/categories`

- **인증**: 불필요 (공개 API)
- **HTTP 응답**: `ApiResponse<BoardCategoryItem[]>` (wrapper 포함)
- **FE `serverFetch<BoardCategoryItem[]>` 수신값**: `body.data` unwrap 이후 타입

```json
{
  "header": { "success": true, "code": "SUCCESS", "message": "요청이 성공적으로 처리되었습니다." },
  "body": {
    "data": [
      { "id": "BCAT_00000001", "category_name": "선사", "sort_order": 0 },
      { "id": "BCAT_00000002", "category_name": "삼국", "sort_order": 1 },
      { "id": "BCAT_00000003", "category_name": "고려", "sort_order": 2 },
      { "id": "BCAT_00000004", "category_name": "조선", "sort_order": 3 }
    ]
  }
}
```

---

## 5. 마이그레이션 계획

| 순서 | 파일명 | 내용 |
|------|--------|------|
| 1 | `sfr108_enable_category_yn.py` | 커뮤니티 3개 게시판 `category_yn=true` |
| 2 | `sfr108_seed_board_categories.py` | 선사/삼국/고려/조선 시드 (12개) |

**revision 체인:**
- 파일 1 `sfr108_enable_category_yn`: `down_revision = "d80be6b751d2"`
- 파일 2 `sfr108_seed_board_categories`: `down_revision = "<파일 1 revision>"` (순차 체인)

---

## 6. 변경 파일

### BE
| 파일 | 유형 |
|------|------|
| `alembic/versions/sfr108_enable_category_yn.py` | 신규 |
| `alembic/versions/sfr108_seed_board_categories.py` | 신규 |
| `app/board/schemas.py` | 수정 (BoardCategoryResponse 추가) |
| `app/board/repository.py` | 수정 (카테고리 조회 메서드 추가) |
| `app/board/service.py` | 수정 (카테고리 서비스 메서드 추가) |
| `app/board/router.py` | 수정 (GET 카테고리 엔드포인트 추가) |
| `app/board/post_schemas.py` | 수정 (category_id 필드 추가) |
| `app/board/post_service.py` | 수정 (category_id 처리) |

### FE
| 파일 | 유형 |
|------|------|
| `apps/client/app/shared/api/endpoints.ts` | 수정 |
| `apps/client/app/shared/types/post.ts` | 수정 (BoardCategoryItem 추가) |
| `apps/client/app/routes/_layout.community.write.tsx` | 수정 |
| `apps/client/app/views/community/CommunityWriteView.tsx` | 수정 |

---

## 7. 성공 기준

- [ ] `GET /api/v1/boards/translation/categories` → 선사/삼국/고려/조선 4개 반환
- [ ] 글 작성 시 `category_id` action POST body 포함 → DB에 저장
- [ ] 카테고리 미선택 상태로 글 작성 가능 (category_id=null)
- [ ] 다른 게시판의 `category_id`로 글 작성 → 400 반환
- [ ] write 페이지에서 글 유형 선택 시 해당 시대 드롭다운 표시
- [ ] 카테고리 API 일부 실패 시 해당 board만 빈 배열, 화면 유지
- [ ] lint + mypy (BE) 통과
- [ ] lint + typecheck (FE) 통과
