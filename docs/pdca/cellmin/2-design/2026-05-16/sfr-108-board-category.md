# Design: 게시판 카테고리 API 구현 (sfr-108-board-category)

**작성자**: cellmin  
**날짜**: 2026-05-16  
**기준 Plan**: `docs/pdca/cellmin/1-plan/2026-05-16/sfr-108-board-category.md`

---

## 1. 아키텍처 개요

```
[BE]
Alembic 마이그레이션
  → category_yn=true (3개 게시판)
  → BoardCategory 시드 (12개)

GET /api/v1/boards/{board_code}/categories
  → BoardRepository.get_categories_by_board_code()
  → BoardCategoryResponse[] 반환 (인증 불필요)

POST /api/v1/posts (기존)
  → PostCreateRequest + category_id (optional)
  → Post.category_id 저장

[FE]
write loader
  → 기존 writableBoards 조회
  → Promise.all(boards.map → BOARD_CATEGORIES(board_code)) 병렬 조회
  → categories: Record<string, BoardCategoryItem[]> 반환

CommunityWriteView
  → 선택된 board_code → 해당 카테고리 목록 드롭다운 표시
  → category_id 폼 전송 (optional)
```

---

## 2. BE 설계

### 2-1. 마이그레이션

**파일 1**: `sfr108_enable_category_yn.py`

```python
revision = "xxxx_enable"   # alembic autogenerate 시 채번
down_revision = 'd80be6b751d2'

def upgrade():
    op.execute("""
        UPDATE cms_tn_board
        SET category_yn = true
        WHERE board_code IN ('translation', 'questions', 'free')
    """)

def downgrade():
    op.execute("""
        UPDATE cms_tn_board
        SET category_yn = false
        WHERE board_code IN ('translation', 'questions', 'free')
    """)
```

**파일 2**: `sfr108_seed_board_categories.py`

```python
revision = "xxxx_seed"           # alembic autogenerate 시 채번
down_revision = "xxxx_enable"    # 파일 1 revision을 바라봄 (순차 체인)
```

- 각 게시판(translation, questions, free)에 선사/삼국/고려/조선 4개씩 = 12개
- ID 형식: `BCAT_00000001` ~ `BCAT_00000012`
- `ON CONFLICT (id) DO NOTHING` 사용 (이미 존재 시 무시)
- sequence: `SELECT setval('seq_bcat', GREATEST((SELECT last_value FROM seq_bcat), 12), true)`

```python
# board_id는 서브쿼리로 조회
# INSERT INTO cms_tn_board_category (id, board_id, category_name, sort_order, ...)
# SELECT 'BCAT_00000001', id, '선사', 0, ... FROM cms_tn_board WHERE board_code = 'translation'
# ON CONFLICT (id) DO NOTHING
```

---

### 2-2. `app/board/schemas.py` 수정

```python
class BoardCategoryResponse(BaseModel):
    id: str = Field(..., description="카테고리 ID")
    category_name: str = Field(..., description="카테고리 이름")
    sort_order: int = Field(..., description="정렬 순서")

    model_config = {"from_attributes": True}
```

---

### 2-3. `app/board/repository.py` 수정

```python
async def get_categories_by_board_code(self, board_code: str) -> list[BoardCategory]:
    result = await self.db.execute(
        select(BoardCategory)
        .join(Board, BoardCategory.board_id == Board.id)
        .where(
            Board.board_code == board_code,
            Board.use_yn.is_(True),
            Board.del_yn.is_(False),
            Board.category_yn.is_(True),
            BoardCategory.use_yn.is_(True),
            BoardCategory.del_yn.is_(False),
        )
        # 게시판 없거나 category_yn=false이면 빈 배열 반환 (404 아님)
        .order_by(BoardCategory.sort_order)
    )
    return list(result.scalars().all())
```

---

### 2-4. `app/board/service.py` 수정

```python
async def list_categories(self, board_code: str) -> list[BoardCategory]:
    return await self.repo.get_categories_by_board_code(board_code)
```

---

### 2-5. `app/board/router.py` 수정

```python
@router.get(
    "/{board_code}/categories",
    response_model=ApiResponse[list[BoardCategoryResponse]],
    summary="게시판 카테고리 목록",
)
async def list_board_categories(
    board_code: str,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[list[BoardCategoryResponse]]:
    service = BoardService(db)
    categories = await service.list_categories(board_code)
    return ApiResponse.success([BoardCategoryResponse.model_validate(c) for c in categories])
```

> 인증 불필요 — 비로그인 사용자도 카테고리 목록 조회 가능 (글 작성 전 참고 목적)

---

### 2-6. `app/board/post_schemas.py` 수정

```python
class PostCreateRequest(BaseModel):
    board_code: str
    title: str = Field(..., max_length=255)
    content: str
    notice_yn: bool = False
    parent_id: str | None = None
    file_ids: list[str] = Field(default_factory=list)
    category_id: str | None = Field(None, description="게시판 카테고리 ID (optional)")
```

---

### 2-7. `app/board/post_service.py` 수정

`create_post` 내 Post 생성 시 `category_id` 추가:

```python
Post(
    id=await next_id("POST_", self.db),
    ...
    category_id=req.category_id,  # 신규 추가
)
```

`category_id`가 지정된 경우 해당 카테고리가 게시판 소속인지 검증:

```python
if req.category_id:
    # 검증: 존재 여부, board 소속, use_yn/del_yn
    # 없거나 board_id 불일치 → 400 INVALID_CATEGORY
    # use_yn=false or del_yn=true → 400 INVALID_CATEGORY
    # board.category_yn=false인데 category_id 지정 → 400 CATEGORY_NOT_ALLOWED
    category = await self._get_category(req.category_id, board.id)
```

---

## 3. FE 설계

### 3-1. `apps/client/app/shared/api/endpoints.ts` 수정

```ts
BOARD_CATEGORIES: (boardCode: string) => `/api/v1/boards/${boardCode}/categories`,
```

---

### 3-2. `apps/client/app/shared/types/post.ts` 수정

```ts
export type BoardCategoryItem = {
    id: string;
    category_name: string;
    sort_order: number;
};
```

---

### 3-3. `apps/client/app/routes/_layout.community.write.tsx` 수정

**action에 `category_id` 추가:**

```ts
const category_id = String(formData.get('category_id') ?? '').trim() || null;

const post = await serverFetch<PostDetail>(request, API_ENDPOINTS.POSTS, {
    method: 'POST',
    body: JSON.stringify({ board_code, title, content, category_id }),
});
```

> 미선택(`''`) → `null` 변환. BE는 `null`을 optional로 허용.

**loader에서 카테고리 병렬 조회:**

```ts
// 카테고리 조회 (boards 조회 성공 시)
let categoryMap: Record<string, BoardCategoryItem[]> = {};
if (writableBoards.length > 0) {
    const results = await Promise.allSettled(
        writableBoards.map(async (b) => {
            const cats = await serverFetch<BoardCategoryItem[]>(
                request,
                API_ENDPOINTS.BOARD_CATEGORIES(b.board_code),
            );
            return { board_code: b.board_code, categories: cats };
        })
    );
    for (const r of results) {
        if (r.status === 'fulfilled') {
            categoryMap[r.value.board_code] = r.value.categories;
        }
    }
}

return { boards: writableBoards, user, defaultBoard, categories: categoryMap };
```

---

### 3-4. `apps/client/app/views/community/CommunityWriteView.tsx` 수정

**"시대" 드롭다운**: 라디오 버튼 그룹 아래에 추가

```tsx
const { boards, defaultBoard, categories } = useLoaderData<typeof loader>();

// 현재 선택된 board_code를 추적 (라디오 → onChange로 갱신)
const [selectedBoard, setSelectedBoard] = useState(defaultBoard);
const currentCategories = categories[selectedBoard] ?? [];
```

```tsx
{/* 시대 선택 — 카테고리가 있는 경우에만 표시 */}
{currentCategories.length > 0 && (
    <div>
        <label htmlFor="category_id" className="block mb-1 text-sm font-medium text-gray-700">
            시대
        </label>
        <select
            key={selectedBoard}
            id="category_id"
            name="category_id"
            className="w-full px-4 py-2 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-transparent"
        >
            <option value="">선택 안 함</option>
            {currentCategories.map(c => (
                <option key={c.id} value={c.id}>{c.category_name}</option>
            ))}
        </select>
    </div>
)}
```

> `key={selectedBoard}` — board 변경 시 select DOM 재생성으로 이전 선택값 자동 초기화.  
> 라디오 버튼 onChange 시 `setSelectedBoard(b.board_code)` → 해당 카테고리로 드롭다운 갱신.

---

## 4. 데이터 흐름

```
[글 작성 진입]
loader → writableBoards 조회
      → Promise.allSettled(boards.map → BOARD_CATEGORIES) 병렬
      → { boards, defaultBoard, categories: { translation: [...], questions: [...], free: [...] } }

[라디오 선택]
onChange → setSelectedBoard(board_code)
         → currentCategories = categories[board_code] → 드롭다운 갱신

[폼 제출]
board_code (radio)  →
category_id (select, optional) →  action → POST /api/v1/posts
title, content      →
```

---

## 5. 엣지 케이스

| 케이스 | 처리 |
|--------|------|
| 카테고리 API 실패 | `Promise.allSettled` — 실패한 board는 빈 배열, 다른 board 정상 표시 |
| 카테고리 없는 board | 드롭다운 미표시 |
| category_id 미선택 | `''` → action에서 null로 처리, BE optional |
| 잘못된 category_id | BE에서 400 반환 → action error 표시 |

---

## 6. 테스트 시나리오

| # | 시나리오 | 기대 |
|---|----------|------|
| T-1 | `GET /api/v1/boards/translation/categories` | 선사/삼국/고려/조선 4개 반환 |
| T-2 | 글 작성 페이지 진입 | 글 유형 아래 "시대" 드롭다운 표시 |
| T-3 | 글 유형 변경 | 해당 게시판 카테고리로 드롭다운 갱신 |
| T-4 | 시대 선택 후 글 작성 | DB에 category_id 저장 확인 |
| T-5 | 시대 미선택 후 글 작성 | category_id=null로 정상 저장 |
| T-6 | 다른 게시판의 category_id로 글 작성 | 400 INVALID_CATEGORY |
| T-7 | 존재하지 않는 category_id로 글 작성 | 400 INVALID_CATEGORY |
| T-8 | 카테고리 미선택 시 action payload 확인 | category_id=null 전송 |
| T-9 | 카테고리 API 일부 실패 | 해당 board만 빈 배열, 글쓰기 화면 유지 |
