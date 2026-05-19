# Design: 커뮤니티 글 작성 화면 UI 정렬 (#100)

**작성자**: cellmin  
**날짜**: 2026-05-14  
**관련 Plan**: `docs/pdca/cellmin/1-plan/2026-05-11/community-write.md`

---

## 1. 아키텍처 개요

변경 범위는 FE 3개 파일에 한정. 서버/API 계약 변경 없음.

```
CommunityListView  ──navigate('/community/write?board=')──▶  write loader
                                                               │
                                                         ?board 파싱
                                                         defaultBoard 결정
                                                               │
                                                       CommunityWriteView
                                                       (라디오 버튼 그룹)
```

---

## 2. 파일별 설계

### 2-1. `apps/client/app/routes/_layout.community.write.tsx`

**변경 대상**: loader 반환값에 `defaultBoard` 추가, 비로그인 redirect URL 수정

```ts
export async function loader({ request }: Route.LoaderArgs) {
    const url = new URL(request.url);

    let user: User | null = null;
    try { user = await serverFetch<User>(request, API_ENDPOINTS.ME); } catch {}

    // 비로그인: pathname + search 그대로 redirect에 포함 → ?board 유지
    if (!user) {
        const redirectTo = encodeURIComponent(url.pathname + url.search);
        throw redirect(`/login?redirect=${redirectTo}`);
    }

    let writableBoards: BoardSummary[] = [];
    try {
        const boardsData = await serverFetch<PageResult<BoardSummary>>(
            request,
            API_ENDPOINTS.BOARDS_LIST,
            { method: 'POST', body: JSON.stringify({ board_group: 'community', page: 1, size: 100 }) },
        );
        writableBoards = boardsData.items.filter(b => b.write_yn);
    } catch {}

    // ?board 파싱 → 유효하면 해당 board_code, 아니면 첫 번째 board
    const boardParam = url.searchParams.get('board') ?? '';
    const matched = writableBoards.find(b => b.board_code === boardParam);
    const defaultBoard = matched?.board_code ?? writableBoards[0]?.board_code ?? '';

    return { boards: writableBoards, user, defaultBoard };
}
```

**변경 없는 부분**: action, meta, route component

---

### 2-2. `apps/client/app/views/community/CommunityWriteView.tsx`

**변경 대상**: 글 유형 `<select>` → 라디오 버튼 그룹, 레이아웃, 헤더 스타일

#### 레이아웃 구조

```
<div class="page-wrapper py-8">
  <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">   ← max-w-3xl → max-w-4xl
    <Link 목록으로 />

    <div class="bg-white rounded-lg shadow-sm border">
      <!-- 회색 헤더 영역 (신규) -->
      <div class="border-b bg-gray-50 px-6 py-4">
        <h1>글 작성하기</h1>
      </div>

      <!-- 폼 본문 -->
      <Form class="p-6 space-y-5">
        <!-- 글 유형 라디오 그룹 -->
        <!-- 제목 -->
        <!-- 내용 -->
        <!-- 에러 -->
        <!-- 버튼 -->
      </Form>
    </div>
  </div>
</div>
```

#### 글 유형 라디오 버튼 그룹

- `boards` 배열을 동적 렌더링 (하드코딩 금지)
- `<input type="radio" name="board_code">` — 브라우저 폼 검증 활용
- `defaultChecked`: `b.board_code === defaultBoard` (첫 렌더 한 번만 적용)
- 선택된 버튼: `bg-blue-600 text-white`, 미선택: `bg-gray-100 text-gray-700`
- `boards.length === 0` 시: 안내 텍스트 표시 + 제출 버튼 `disabled`

```tsx
{/* 글 유형 */}
<div>
  <label className="block text-sm font-medium text-gray-700 mb-2">
    글 유형 <span className="text-red-500">*</span>
  </label>

  {boards.length === 0 ? (
    <p className="text-sm text-gray-500">게시판 정보를 불러오지 못했습니다.</p>
  ) : (
    // key={defaultBoard}: defaultBoard 변경 시 라디오 그룹 재마운트 → defaultChecked 재동기화
    <div key={defaultBoard} role="group" aria-label="글 유형" className="flex flex-wrap gap-2">
      {boards.map((b) => (
        <label key={b.board_code} className="cursor-pointer">
          <input
            type="radio"
            name="board_code"
            value={b.board_code}
            defaultChecked={b.board_code === defaultBoard}
            required
            className="sr-only peer"
          />
          <span className="inline-flex items-center px-4 py-2 rounded-lg font-medium transition-colors
                           bg-gray-100 text-gray-700
                           peer-checked:bg-blue-600 peer-checked:text-white
                           peer-focus-visible:ring-2 peer-focus-visible:ring-blue-600 peer-focus-visible:ring-offset-2">
            {b.board_name}
          </span>
        </label>
      ))}
    </div>
  )}
</div>
```

> **접근성**: `sr-only`로 radio input 시각적으로 숨기고 `peer` + `peer-checked` 조합으로 스타일 연동. `role="group"` + `aria-label`로 스크린리더 지원. `peer-focus-visible:ring-*`으로 키보드 포커스 표시.

#### 제출 버튼 비활성화 조건

```tsx
<button
  type="submit"
  disabled={isSubmitting || boards.length === 0}
  ...
>
```

---

### 2-3. `apps/client/app/views/community/CommunityListView.tsx`

**변경 대상**: 글 작성 버튼 navigate 경로에 `?board=` 추가

```ts
// writePath 공통 계산 (encodeURIComponent로 board code 안전 처리)
const writePath = currentTab === 'all'
    ? '/community/write'
    : `/community/write?board=${encodeURIComponent(currentTab)}`;

// 비로그인: openModal 확인 버튼 안의 navigate URL 변경 (기존 구조 유지)
if (!user) {
    openModal({
        type: 'alert',
        message: '로그인이 필요한 서비스입니다.',
        buttons: [{ label: '확인', onClick: () => navigate(`/login?redirect=${encodeURIComponent(writePath)}`) }],
    });
    return;
}

// 로그인: writePath로 직접 이동
navigate(writePath);
```

---

## 3. 데이터 흐름

```
loader 반환값
├── boards: BoardSummary[]   (기존 유지)
├── user: User               (기존 유지)
└── defaultBoard: string     (신규 — ?board 파싱 결과)

Form 제출값 (action contract 변경 없음)
├── board_code: string   ← radio input name="board_code"
├── title: string
└── content: string
```

---

## 4. 엣지 케이스 처리

| 케이스 | 처리 |
|--------|------|
| `?board` 없음 | `boards[0].board_code` 기본 선택 |
| `?board` 유효하지 않은 값 | `boards[0].board_code` fallback |
| `boards` 빈 배열 (API 실패) | 안내 메시지 + 제출 버튼 비활성화 |
| 비로그인 접근 | `pathname + search` 포함 redirect → 로그인 후 `?board` 유지 |
| `tab=all`에서 글 작성 클릭 | `?board` 없이 이동 → `boards[0]` 기본 선택 |

---

## 5. 테스트 시나리오 (브라우저 수동)

| # | 시나리오 | 기대 결과 |
|---|----------|-----------|
| T-1 | 목록 "번역" 탭 → 글 작성 클릭 | 번역 버튼 선택된 상태로 write 진입 |
| T-2 | 목록 "전체" 탭 → 글 작성 클릭 | 첫 번째 board(번역) 선택 |
| T-3 | `/community/write?board=free` 직접 입력 | 자유 버튼 선택 |
| T-4 | `/community/write?board=invalid` 직접 입력 | 첫 번째 board(번역) 선택 |
| T-5 | 비로그인 → `/community/write?board=questions` | 로그인 후 질문 선택된 채로 복귀 |
| T-6 | 글 유형 선택 → 제목/내용 입력 → 제출 | 상세 페이지로 이동 |
| T-7 | boards 빈 배열 (API 실패 시뮬레이션) | 안내 메시지 표시, 제출 버튼 비활성화 |
