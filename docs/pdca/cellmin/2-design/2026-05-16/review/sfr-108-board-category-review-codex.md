# Review: 게시판 카테고리 API 구현 Design (sfr-108-board-category)

**리뷰어**: Codex  
**리뷰일**: 2026-05-16  
**대상 문서**: `docs/pdca/cellmin/2-design/2026-05-16/sfr-108-board-category.md`

---

## 총평

Design은 BE repository/service/router, FE loader/UI까지 구현 경로를 잘 나누고 있다. 다만 현재 코드베이스와 대조했을 때 `ApiResponse.ok` 사용, FE action 누락, migration revision 체인, 조회/저장 검증 조건에서 수정이 필요하다. 이 항목들은 구현 단계에서 바로 실패하거나 선택한 카테고리가 저장되지 않는 문제로 이어질 수 있다.

---

## 주요 Findings

### 1. High - `ApiResponse.ok(...)`는 현재 코드베이스에 존재하지 않음

Design의 router 예시는 `ApiResponse.ok(...)`를 사용한다. 현재 공통 응답 클래스에는 `success`, `created`, `updated`, `deleted`, `error`만 있다. 그대로 구현하면 런타임 에러가 발생한다.

**문제 예시**

```python
return ApiResponse.ok([BoardCategoryResponse.model_validate(c) for c in categories])
```

**권장 수정**

```python
return ApiResponse.success([BoardCategoryResponse.model_validate(c) for c in categories])
```

---

### 2. High - FE action의 `category_id` 처리 설계가 빠져 있음

Design은 loader에서 카테고리를 조회하고 `CommunityWriteView`에서 `<select name="category_id">`를 렌더링하는 내용은 포함한다. 하지만 form submit을 처리하는 action에서 `category_id`를 읽고 POST body에 넣는 설계가 없다.

현재 구현 구조상 action이 body에 넣지 않으면 BE가 `category_id`를 받을 수 없다.

**권장 추가 설계**

```ts
const category_id = String(formData.get('category_id') ?? '').trim() || null;

const post = await serverFetch<PostDetail>(request, API_ENDPOINTS.POSTS, {
    method: 'POST',
    body: JSON.stringify({ board_code, title, content, category_id }),
});
```

미선택 정책은 `null` 전송 또는 필드 생략 중 하나로 통일한다. 현재 문서의 엣지 케이스가 `'' -> null`을 말하고 있으므로 action에서 `null` 변환을 명시하는 것이 좋다.

---

### 3. Medium - Alembic 두 번째 파일의 `down_revision`이 불명확함

Design은 첫 번째 migration에만 `down_revision = 'd80be6b751d2'`를 보여준다. 두 번째 seed migration의 `down_revision`은 첫 번째 migration의 revision을 바라봐야 한다. 그렇지 않으면 migration head가 갈라질 수 있다.

**권장 구조**

```python
# sfr108_enable_category_yn.py
revision = "..."
down_revision = "d80be6b751d2"

# sfr108_seed_board_categories.py
revision = "..."
down_revision = "<sfr108_enable_category_yn revision>"
```

---

### 4. Medium - 카테고리 목록 조회 조건이 충분하지 않음

repository 예시는 다음 조건만 사용한다.

```python
Board.board_code == board_code,
Board.use_yn.is_(True),
BoardCategory.use_yn.is_(True),
BoardCategory.del_yn.is_(False),
```

soft-delete된 게시판과 카테고리 기능이 꺼진 게시판을 배제하려면 `Board.del_yn.is_(False)`와 `Board.category_yn.is_(True)`를 추가하는 편이 안전하다.

**권장 수정**

```python
.where(
    Board.board_code == board_code,
    Board.use_yn.is_(True),
    Board.del_yn.is_(False),
    Board.category_yn.is_(True),
    BoardCategory.use_yn.is_(True),
    BoardCategory.del_yn.is_(False),
)
```

게시판이 없거나 카테고리 기능이 꺼진 경우 404/빈 배열 중 어떤 정책을 택할지도 명시하는 것이 좋다. 현재 "카테고리 목록 반환" 목적이라면 빈 배열이 FE 처리에는 단순하다.

---

### 5. Medium - 글 작성 시 카테고리 검증 구현 위치가 추상적임

Design은 `_get_category(req.category_id, board.id)` 정도만 언급한다. 실제 구현 리스크를 줄이려면 repository 메서드 또는 service private 메서드의 검증 조건과 에러 코드를 문서에 명시하는 편이 좋다.

**권장 명시**

- `category_id`가 존재하지 않으면 400 `INVALID_CATEGORY`
- 카테고리의 `board_id`가 작성 대상 board와 다르면 400 `INVALID_CATEGORY`
- `use_yn=false` 또는 `del_yn=true`이면 400 `INVALID_CATEGORY`
- `board.category_yn=false`인데 `category_id`가 들어오면 400 `CATEGORY_NOT_ALLOWED`

---

### 6. Low - seed migration의 고정 ID와 `setval` 정책이 개발 DB에서 취약할 수 있음

Design은 `BCAT_00000001`부터 `BCAT_00000012`까지 고정 ID를 넣고 `setval('seq_bcat', 12, true)`를 수행한다. 신규 DB에서는 문제 없지만, 일부 데이터가 이미 있는 개발 DB에서는 sequence가 뒤로 이동할 수 있다.

**권장 보완**

- `ON CONFLICT (id) DO NOTHING`을 사용한다.
- sequence는 현재 값과 12 중 큰 값으로 맞춘다.
- 가능하면 기존 `next_id("BCAT_")` 규칙과 충돌하지 않는 seed 전략을 명시한다.

예:

```sql
SELECT setval('seq_bcat', GREATEST((SELECT last_value FROM seq_bcat), 12), true);
```

---

### 7. Low - UI 상태 전환 시 선택된 category 초기화 정책이 필요함

라디오로 board를 바꿀 때 기존 board에서 선택한 `category_id`가 남아 있으면 다른 board의 카테고리가 제출될 수 있다. React가 select를 새로 렌더링하면서 자연히 초기화될 수도 있지만, 상태/DOM 구조에 따라 명시적 초기화가 더 안전하다.

**권장 보완**

- `selectedBoard` 변경 시 category select를 빈 값으로 초기화한다.
- 또는 `<select key={selectedBoard}>`를 사용해 board 변경 시 select DOM을 재생성한다.

---

## 테스트 보완 제안

현재 테스트 시나리오 T-1~T-5에 아래 케이스를 추가하는 것을 권장한다.

| # | 시나리오 | 기대 |
|---|----------|------|
| T-6 | 다른 게시판의 `category_id`로 글 작성 | 400 `INVALID_CATEGORY` |
| T-7 | 존재하지 않는 `category_id`로 글 작성 | 400 `INVALID_CATEGORY` |
| T-8 | 카테고리 미선택 후 action payload 확인 | `category_id=null` 또는 필드 미포함 |
| T-9 | 카테고리 API 일부 실패 | 해당 board만 빈 배열, 글쓰기 화면은 유지 |

---

## 수정 권장 요약

- `ApiResponse.ok`를 `ApiResponse.success`로 변경
- FE action의 `category_id` form parsing 및 POST body 포함 설계 추가
- 두 migration의 revision 체인 명확화
- 카테고리 조회 조건에 `Board.del_yn`, `Board.category_yn` 추가
- 글 작성 시 category 검증 조건과 에러 코드 명시
- board 변경 시 category 선택 초기화 정책 추가

