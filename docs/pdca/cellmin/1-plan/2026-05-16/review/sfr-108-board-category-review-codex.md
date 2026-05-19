# Review: 게시판 카테고리 API 구현 Plan (sfr-108-board-category)

**리뷰어**: Codex  
**리뷰일**: 2026-05-16  
**대상 문서**: `docs/pdca/cellmin/1-plan/2026-05-16/sfr-108-board-category.md`

---

## 총평

Plan의 범위는 BE API, 마이그레이션, FE 글쓰기 화면 연동까지 잘 잡혀 있다. 다만 구현 시 바로 장애로 이어질 수 있는 지점이 몇 가지 있다. 특히 FE action의 `category_id` 전송, API 응답 wrapper 표기, Alembic revision 체인 명시는 보완이 필요하다.

---

## 주요 Findings

### 1. High - FE action에서 `category_id` 전송 요구가 명확하지 않음

요구사항 F-4는 "선택 시 `category_id` 전송"이라고 되어 있으나, 변경 파일/성공 기준에는 loader와 UI 중심으로만 정리되어 있다. 현재 코드 기준으로는 action이 `board_code`, `title`, `content`만 POST body에 넣고 있어, 드롭다운을 추가해도 DB에 저장되지 않을 수 있다.

**권장 보완**

- FE 변경 파일 설명에 `_layout.community.write.tsx` action 수정 포함을 명시한다.
- 성공 기준에 "action POST body에 `category_id` 포함"을 추가한다.
- 미선택 시 `null` 또는 필드 생략 중 하나를 표준으로 정한다.

예:

```ts
const category_id = String(formData.get('category_id') ?? '').trim() || null;
body: JSON.stringify({ board_code, title, content, category_id })
```

---

### 2. High - API 응답 형태가 실제 공통 wrapper와 다르게 읽힘

Plan의 API 설계는 응답을 `BoardCategoryItem[]` raw array처럼 표현한다. 하지만 현재 클라이언트 `serverFetch`는 `{ header, body: { data } }` 형태의 `ApiResponse`를 unwrap하는 구조다. 문서만 보고 BE 테스트나 curl 검증을 만들면 실제 응답 형태와 어긋날 수 있다.

**권장 보완**

- HTTP 실제 응답은 `ApiResponse<BoardCategoryItem[]>`로 적는다.
- FE에서 `serverFetch<BoardCategoryItem[]>`로 받는 값은 `body.data` unwrap 이후 타입이라고 구분한다.

예:

```json
{
  "header": { "success": true, "code": "SUCCESS", "message": "요청이 성공적으로 처리되었습니다." },
  "body": {
    "data": [
      { "id": "BCAT_00000001", "category_name": "선사", "sort_order": 0 }
    ]
  }
}
```

---

### 3. Medium - Alembic migration 체인 명시가 부족함

Plan은 migration 두 개를 만들겠다고 하면서 `down_revision: d80be6b751d2`를 하나만 명시한다. 두 파일이 모두 같은 `down_revision`을 바라보면 multiple heads가 생기거나 실행 순서가 불명확해질 수 있다.

**권장 보완**

- 첫 번째 migration: `down_revision = "d80be6b751d2"`
- 두 번째 migration: `down_revision = "<첫 번째 migration revision>"`

또는 하나의 migration으로 합쳐서 `category_yn` 활성화와 seed를 순차 처리하는 방식도 가능하다.

---

### 4. Medium - 카테고리 검증 요구가 Plan에 빠져 있음

B-4는 `PostCreateRequest.category_id` 추가만 언급한다. 그러나 글 작성 시 전달된 `category_id`가 현재 게시판 소속인지 검증하지 않으면 다른 게시판 카테고리를 연결할 수 있다.

**권장 보완**

BE 요구사항에 다음 검증을 추가한다.

- `category_id`가 있으면 해당 카테고리가 존재해야 한다.
- 카테고리의 `board_id`가 작성 대상 게시판과 같아야 한다.
- `BoardCategory.use_yn=true`, `BoardCategory.del_yn=false`여야 한다.
- 필요 시 `Board.category_yn=true`인 게시판에서만 카테고리 저장을 허용한다.

---

### 5. Low - 카테고리 조회 실패 시 UX/정책이 성공 기준에 없음

비기능 요구사항에는 "boards가 없으면 카테고리 조회 없이 빈 배열 반환"만 있다. 카테고리 API 일부 실패 시 화면을 계속 보여줄지, 작성 자체를 막을지 정책이 Plan에는 없다.

**권장 보완**

- 카테고리 API 일부 실패 시 해당 board의 카테고리는 빈 배열로 처리한다.
- 글 작성은 카테고리 미선택 가능 정책에 따라 계속 허용한다.

---

## 보완 권장 체크리스트

- [ ] Plan의 API 응답 예시를 `ApiResponse` wrapper 기준으로 수정
- [ ] FE action에서 `category_id`를 POST body에 포함한다고 명시
- [ ] Alembic migration 2개 각각의 revision/down_revision 관계 명시
- [ ] `category_id` 게시판 소속 검증 요구사항 추가
- [ ] 잘못된 `category_id`, 다른 게시판 `category_id`, 미선택 케이스를 성공 기준 또는 테스트에 추가

