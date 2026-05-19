# Design — community-api-connect

> **Redmine:** #104 · **날짜:** 2026-05-04 · **작업자:** cellmin

---

## 1. 아키텍처

### 데이터 흐름

```
/community 진입
  └─▶ loader
        ├─▶ POST /api/v1/boards/list  { board_group: 'community' }  → 탭 목록
        └─▶ POST /api/v1/posts/list   { board_codes: [...] }       → 게시글 목록

/community/:id 진입
  └─▶ loader (Promise.all)
        ├─▶ GET  /api/v1/posts/{id}                                 → 게시글 단건
        └─▶ POST /api/v1/posts/{id}/comments/list                   → 댓글 목록
  └─▶ action (댓글 작성)
        └─▶ POST /api/v1/posts/{id}/comments → revalidation → 댓글 갱신

/community/write 진입
  └─▶ loader → 게시판 목록 조회  { board_group: 'community' }  (write_yn=true 필터)
  └─▶ action (게시글 작성)
        └─▶ POST /api/v1/posts → redirect /community/{id}
```

### 레이어 역할

| 레이어 | 역할 |
|--------|------|
| `routes/` | loader (서버 fetch) + action (뮤테이션) |
| `views/` | `useLoaderData()` 소비, UI 렌더링 |
| `shared/api/` | 엔드포인트 상수, serverFetch 유틸 |
| `shared/types/` | BE 응답 타입 정의 |

---

## 2. BE 변경 설계

### 2-1. `cms_tn_board` 테이블 — `board_group` 컬럼 추가

```sql
ALTER TABLE cms_tn_board ADD COLUMN board_group VARCHAR(50) DEFAULT NULL;
UPDATE cms_tn_board SET board_group = 'community'
    WHERE board_code IN ('translation', 'questions', 'free');
```

- 커뮤니티 게시판: `board_group = 'community'`
- 나중에 다른 그룹 게시판 추가 시 `board_group = 'notice'` 등 자유롭게 확장

### 2-2. `BoardListRequest` — `board_group` 필터 추가

```python
class BoardListRequest(BaseModel):
    board_group: str | None = Field(None, description="그룹 필터 (예: 'community')")
    page: int = Field(1, ge=1)
    size: int = Field(20, ge=1, le=100)
```

### 2-3. `BoardSummaryResponse` — `board_group`, `write_yn` 필드 추가

```python
class BoardSummaryResponse(BaseModel):
    ...
    write_yn: bool = Field(..., description="로그인 사용자 쓰기 허용")
    board_group: str | None = Field(None, description="게시판 그룹")
```

> `write_yn`은 `/community/write` 게시판 선택 셀렉트에서 작성 불가 게시판을 제외하는 데 사용

### 2-4. `PostListRequest` — `board_code` → `board_codes` 변경

```python
class PostListRequest(BaseModel):
    board_codes: list[str] = Field(..., description="게시판 코드 목록", min_length=1)
    keyword: str | None = None
    page: int = Field(1, ge=1)
    size: int = Field(20, ge=1, le=100)
```

### 2-5. `PostRepository.list()` — `IN` 쿼리 적용

```python
async def list(
    self,
    board_ids: list[str],   # 변경: str → list[str]
    keyword: str | None,
    page: int,
    size: int,
) -> tuple[list[Post], int]:
    conditions = [
        Post.board_id.in_(board_ids),   # 변경: == → in_()
        Post.del_yn.is_(False),
        Post.parent_id.is_(None),
    ]
    ...
```

### 2-6. `PostService.list_posts()` — board_ids 목록 조회

```python
# board_codes 리스트 → board_ids 리스트로 변환
boards = await self.board_repo.get_by_codes(req.board_codes)
board_ids = [b.id for b in boards]
posts, total = await self.post_repo.list(board_ids, req.keyword, req.page, req.size)
```

> `get_by_codes()`는 `use_yn=true`, `del_yn=false` 게시판만 반환하고, 목록 API의 기존 권한 정책과 동일하게 비로그인은 `guest_read_yn=true`, 로그인 사용자는 `read_yn=true` 조건을 적용한다.

---

## 3. FE 타입 설계

### `shared/types/post.ts`

```ts
// BE API 응답 타입
export type BoardSummary = {
    id: string;
    board_code: string;
    board_name: string;
    board_type: string;
    guest_read_yn: boolean;
    write_yn: boolean;
    board_group: string | null;
    sort_order: number;
    use_yn: boolean;
};

// 커뮤니티 탭 타입: 'all' 또는 동적 board_code
// PostTab = 'all' | string 은 사실상 string이므로 제거.
// loader/view에서 currentTab: string으로 사용하고, 'all' 여부만 비교한다.
// (예: const isAll = tab === 'all')

export type PostSummary = {
    id: string;
    board_id: string;
    board_code: string;
    author_name: string;
    is_ai_gen: boolean;
    title: string;
    notice_yn: boolean;
    view_count: number;
    comment_count: number;
    created_at: string;
};

export type PostDetail = {
    id: string;
    board_id: string;
    board_code: string;
    user_id: string;
    author_name: string;
    is_ai_gen: boolean;
    parent_id: string | null;
    depth: number;
    title: string;
    content: string;
    notice_yn: boolean;
    view_count: number;
    comment_count: number;
    auto_reply_status: string;
    files: unknown[];
    created_at: string;
    updated_at: string;
};

export type CommentItem = {
    id: string;
    post_id: string;
    user_id: string | null;
    author_name: string | null;
    is_ai_gen: boolean;
    is_deleted: boolean;
    parent_id: string | null;
    depth: number;
    content: string;
    created_at: string;
    updated_at: string;
    replies: CommentItem[];
};
```

---

## 4. FE API 엔드포인트

### `shared/api/endpoints.ts`

```ts
BOARDS_LIST: '/api/v1/boards/list',
POSTS: '/api/v1/posts',           // 게시글 작성 POST
POSTS_LIST: '/api/v1/posts/list',
POST: (id: string) => `/api/v1/posts/${id}`,
POST_COMMENTS_LIST: (id: string) => `/api/v1/posts/${id}/comments/list`,
POST_COMMENTS: (id: string) => `/api/v1/posts/${id}/comments`,
```

---

## 5. 코드 구조 설계

### `routes/_layout.community._index.tsx` — loader

```ts
export async function loader({ request }: Route.LoaderArgs) {
    const url = new URL(request.url);
    const tab  = url.searchParams.get('tab') ?? 'all';
    const page = Math.max(1, Number(url.searchParams.get('page')) || 1);

    let user: User | null = null;
    try { user = await serverFetch<User>(request, API_ENDPOINTS.ME); } catch {}

    // 1. 커뮤니티 게시판 목록 동적 조회
    const boardsData = await serverFetch<PageResult<BoardSummary>>(
        request, API_ENDPOINTS.BOARDS_LIST,
        { method: 'POST', body: JSON.stringify({ board_group: 'community', page: 1, size: 100 }) }
    );
    const boards = boardsData.items;

    // 2. 탭에 해당하는 board_codes 결정
    //    유효하지 않은 tab이면 'all'로 fallback (빈 배열 → BE 422 방지)
    const matchedCodes = boards.filter(b => b.board_code === tab).map(b => b.board_code);
    const effectiveTab = tab === 'all' || matchedCodes.length === 0 ? 'all' : tab;
    const boardCodes = effectiveTab === 'all'
        ? boards.map(b => b.board_code)
        : matchedCodes;

    // 3. 게시글 목록 조회 (단일 API, IN 쿼리)
    const data = await serverFetch<PageResult<PostSummary>>(
        request, API_ENDPOINTS.POSTS_LIST,
        { method: 'POST', body: JSON.stringify({ board_codes: boardCodes, page, size: 20 }) }
    );

    return { boards, posts: data.items, total: data.total, page: data.page, size: data.size, user };
}
```

### `routes/_layout.community.$id.tsx` — loader + action

```ts
// loader: 게시글 단건 + 댓글 병렬 조회
export async function loader({ params, request }: Route.LoaderArgs) {
    const { id } = params;
    if (!id) throw redirect('/community');

    let user: User | null = null;
    try { user = await serverFetch<User>(request, API_ENDPOINTS.ME); } catch {}

    let post: PostDetail | null = null;
    let comments: CommentItem[] = [];
    let accessDenied = false;

    try {
        const [postData, commentsData] = await Promise.all([
            serverFetch<PostDetail>(request, API_ENDPOINTS.POST(id)),
            serverFetch<PageResult<CommentItem>>(request, API_ENDPOINTS.POST_COMMENTS_LIST(id),
                { method: 'POST', body: JSON.stringify({ page: 1, size: 50 }) }
            ),
        ]);
        post = postData;
        comments = commentsData.items;
    } catch (err) {
        if (err instanceof ApiError && err.status === 403) {
            accessDenied = true;
        } else throw err;
    }

    return { post, postId: id, comments: comments ?? [], user, accessDenied };
}

// action: 댓글 작성
export async function action({ params, request }: Route.ActionArgs) {
    const { id } = params;
    const formData = await request.formData();
    const content = String(formData.get('content') ?? '').trim();
    if (!content) return { ok: false, error: '댓글 내용을 입력해주세요.' };

    try {
        await serverFetch(request, API_ENDPOINTS.POST_COMMENTS(id!), {
            method: 'POST',
            body: JSON.stringify({ content }),
        });
        return { ok: true };
    } catch (err) {
        if (err instanceof ApiError) {
            return { ok: false, error: err.message };
        }
        return { ok: false, error: '댓글 작성에 실패했습니다.' };
    }
}
```

### `routes/_layout.community.write.tsx` — loader + action

```ts
// loader: 게시판 목록 (게시판 선택 셀렉트용)
export async function loader({ request }: Route.LoaderArgs) {
    // 비로그인 → 로그인 페이지로
    let user: User | null = null;
    try { user = await serverFetch<User>(request, API_ENDPOINTS.ME); } catch {}
    if (!user) throw redirect('/login?redirect=/community/write');

    const boardsData = await serverFetch<PageResult<BoardSummary>>(
        request, API_ENDPOINTS.BOARDS_LIST,
        { method: 'POST', body: JSON.stringify({ board_group: 'community', page: 1, size: 100 }) }
    );
    // write_yn=true 게시판만 선택 가능하도록 필터
    const writableBoards = boardsData.items.filter(b => b.write_yn);
    return { boards: writableBoards, user };
}

// action: 게시글 작성
export async function action({ request }: Route.ActionArgs) {
    const formData = await request.formData();
    const board_code = String(formData.get('board_code') ?? '');
    const title = String(formData.get('title') ?? '').trim();
    const content = String(formData.get('content') ?? '').trim();

    if (!title || !content || !board_code) {
        return { ok: false, error: '필수 항목을 모두 입력해주세요.' };
    }

    try {
        const post = await serverFetch<PostDetail>(request, API_ENDPOINTS.POSTS, {
            method: 'POST',
            body: JSON.stringify({ board_code, title, content }),
        });
        throw redirect(`/community/${post.id}`);
    } catch (err) {
        if (err instanceof Response) throw err; // redirect
        if (err instanceof ApiError) return { ok: false, error: err.message };
        return { ok: false, error: '게시글 작성에 실패했습니다.' };
    }
}
```

### `views/community/CommunityDetailView.tsx` — useFetcher 패턴

```ts
const fetcher = useFetcher<typeof action>();
const [comment, setComment] = useState('');

// 작성 성공 시 입력창 초기화
useEffect(() => {
    if (fetcher.data?.ok) setComment('');
}, [fetcher.data]);

// JSX
<fetcher.Form method="post">
    <textarea name="content" value={comment} onChange={e => setComment(e.target.value)} />
    {fetcher.data?.error && <p className="text-red-500">{fetcher.data.error}</p>}
    <button disabled={!user || fetcher.state !== 'idle'}>댓글 작성</button>
</fetcher.Form>
```

---

## 6. 날짜 포맷 헬퍼

각 View 파일 내 인라인 사용:

```ts
const formatDate = (iso: string) => {
    const d = new Date(iso);
    return `${d.getFullYear()}.${String(d.getMonth() + 1).padStart(2, '0')}.${String(d.getDate()).padStart(2, '0')}`;
};
```

---

## 7. 주요 설계 결정

| 결정 사항 | 선택 | 이유 |
|-----------|------|------|
| 비로그인 게시판 접근 | 전체 허용 | 3개 게시판 모두 `guest_read_yn = true` |
| 게시판 탭 구성 | boards API 동적 조회 | 게시판 추가 시 FE 코드 변경 불필요 |
| 커뮤니티 게시판 구분 | `board_group = 'community'` 컬럼 | 확장 가능한 그룹 방식 |
| all 탭 전략 | board_codes 리스트 → BE `IN` 쿼리 | 단일 API 호출, 정확한 페이지네이션 |
| 댓글 작성 UX | `useFetcher()` | 전체 페이지 이동 없이 revalidation |
| 상세 403 처리 | catch → accessDenied 반환, `postId` 별도 보존 | View에서 `post`가 null일 수 있음 |
| 댓글 에러 처리 | action에서 catch → `{ ok: false, error }` | 사용자 피드백 제공 |

---

## 8. 영향 범위

### BE 변경 파일

- `alembic/versions/` — `board_group` 컬럼 마이그레이션 신규
- `app/board/models.py` — `Board.board_group` 필드 추가
- `app/board/schemas.py` — `BoardListRequest`, `BoardSummaryResponse` 수정
- `app/board/repository.py` — `board_group` 필터 쿼리 추가, `get_by_codes()` 추가
- `app/board/post_schemas.py` — `PostListRequest.board_codes` 변경
- `app/board/post_repository.py` — `list()` IN 쿼리 적용
- `app/board/post_service.py` — `board_ids` 목록 조회 로직 수정

### FE 변경 파일

- `shared/api/endpoints.ts`
- `shared/types/post.ts`
- `views/community/config.ts` — 하드코딩 제거
- `routes/_layout.community._index.tsx`
- `views/community/CommunityListView.tsx`
- `routes/_layout.community.$id.tsx`
- `views/community/CommunityDetailView.tsx`
- `routes/_layout.community.write.tsx`

### 영향 없는 파일

- `mock.ts`, `mockComments.ts` — import 제거, 파일 유지
