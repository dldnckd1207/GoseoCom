# Design: 커뮤니티 글 상세 페이지 (#99)

**작성일:** 2026-04-30
**작성자:** cellmin

---

## 1. 아키텍처

React Router v7 (SSR) 패턴 그대로 유지.

```
apps/client/app/
├── routes/
│   └── _layout.community.$id.tsx   ← loader (SSR) + meta + default export
├── views/community/
│   ├── CommunityDetailView.tsx      ← UI 전담 (props만 받음, 신규)
│   ├── config.ts                    ← BOARD_CONFIG (신규)
│   ├── mock.ts                      ← MOCK_POSTS에 content, viewCount 추가
│   └── mockComments.ts              ← MOCK_COMMENTS, getComments (신규)
└── shared/types/
    └── post.ts                      ← Post 타입 확장, Comment 타입 신규
```

- loader에서 데이터·권한 처리 → View는 `useLoaderData<typeof loader>()` 직접 호출
- API 전환 시 loader 내부만 교체, View 무변경

---

## 2. 타입 설계

### `shared/types/post.ts` 변경

```ts
// 기존 Post에 추가
export type Post = {
    id: string;
    title: string;
    tab: Exclude<PostTab, 'all'>;
    era: Exclude<PostEra, 'all'>;
    author: string;
    createdAt: string;
    content: string;      // 추가
    viewCount: number;    // 추가
};

// 신규
export type Comment = {
    id: string;
    author: string;
    content: string;
    createdAt: string;
};
```

---

## 3. Mock 데이터 설계

### `views/community/mock.ts` — Post 확장

기존 30개 게시글에 `content`, `viewCount` 추가.
본문은 제목 맥락에 맞는 짧은 더미 텍스트(1~2문단) 공통 템플릿 사용.

```ts
{ id: '1', ..., content: '안녕하세요. ...질문 내용...', viewCount: 124 }
```

### `views/community/mockComments.ts` — 신규

```ts
// 게시글 id → Comment[] 매핑
export const MOCK_COMMENTS: Record<string, Comment[]> = {
    '1': [
        { id: 'c1', author: '역사학도', content: '...', createdAt: '2026.04.15' },
        { id: 'c2', author: '한문전문가', content: '...', createdAt: '2026.04.15' },
    ],
    // 나머지 id는 빈 배열 fallback
};

export const getComments = (postId: string): Comment[] =>
    MOCK_COMMENTS[postId] ?? [];
```

---

## 4. 게시판 설정

### `views/community/config.ts` — 신규

Mock 데이터(`mock.ts`)와 권한 정책은 성격이 다르므로 별도 파일 분리.

```ts
import type { PostTab } from '~/shared/types/post';

export const BOARD_CONFIG: Record<
    Exclude<PostTab, 'all'>,
    { label: string; requiresLogin: boolean }
> = {
    translate: { label: '번역', requiresLogin: false },
    question:  { label: '질문', requiresLogin: true  },
    free:      { label: '자유', requiresLogin: false  },
};
```

---

## 5. 라우트 설계

### `_layout.community.$id.tsx`

```ts
import { redirect, useLoaderData } from 'react-router';

import { API_ENDPOINTS } from '~/shared/api/endpoints';
import { serverFetch } from '~/shared/api/server';
import { BOARD_CONFIG } from '~/views/community/config';
import { getComments } from '~/views/community/mockComments';
import { MOCK_POSTS } from '~/views/community/mock';
import { CommunityDetailView } from '~/views/community/CommunityDetailView';

import type { Route } from './+types/_layout.community.$id';
import type { User } from '~/shared/types/auth';

export async function loader({ params, request }: Route.LoaderArgs) {
    // 1. params.id 확인 후 게시글 조회
    const { id } = params;
    if (!id) throw redirect('/community');

    const post = MOCK_POSTS.find(p => p.id === id);
    if (!post) throw new Response('Not Found', { status: 404 }); // HTTP 404 — GS/보안 요건

    // 2. user 취득 (_layout loader SSR에서 재사용 불가 → 직접 조회)
    //    401 외 네트워크 에러/서버 장애도 비로그인으로 흡수 (_layout 정책과 동일)
    let user: User | null = null;
    try {
        user = await serverFetch<User>(request, API_ENDPOINTS.ME);
    } catch {
        // 인증 조회 실패(401, 네트워크 오류 등) → 비로그인으로 처리
    }

    // 3. 권한 체크
    const boardConfig = BOARD_CONFIG[post.tab];
    const accessDenied = boardConfig.requiresLogin && user === null;

    // 4. 댓글 (접근 불가 시 빈 배열)
    const comments = accessDenied ? [] : getComments(id);

    return { post, boardConfig, accessDenied, comments, user };
}

export function meta({ data }: Route.MetaArgs) {
    return [{ title: `${data?.post.title ?? '게시글'} | 해독 AI` }];
}

export default function CommunityDetailRoute() {
    return <CommunityDetailView />;
}
```

---

## 6. UI 설계

### 레이아웃 구조 (`max-w-4xl mx-auto`)

```
[뒤로가기] ← 목록으로

┌─────────────────────────────────┐
│ [시대 배지]                      │  게시글 카드
│ 제목                             │
│ 작성자 · 날짜 · 조회수           │
├─────────────────────────────────┤
│ 본문 내용                        │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│ 댓글 N                          │  댓글 카드
├─────────────────────────────────┤
│ [댓글 작성 영역]                 │
│   로그인 O → textarea + 버튼    │
│   로그인 X → disabled + 안내    │
├─────────────────────────────────┤
│ 댓글 목록                        │
└─────────────────────────────────┘
```

### accessDenied 화면

```
┌─────────────────────────────────┐
│ 회원 전용 게시판입니다.           │
│ 로그인을 통해 조회해주세요.       │
│                                 │
│  [목록으로]     [로그인하기]     │
└─────────────────────────────────┘
```

- 로그인 버튼: `<Link to={`/login?redirect=/community/${post.id}`}>` — LoginView가 query 값 읽어 처리
- 목록으로: `<Link to="/community">`
- 상세 페이지에서 sessionStorage 직접 조작 안 함

### ERA_LABELS 배지 색상

기존 `CommunityListView`와 동일 (blue-100/blue-700)

### 댓글 작성 — 비로그인

```tsx
<textarea disabled placeholder="로그인 후 댓글을 작성할 수 있습니다." />
<button disabled>댓글 작성</button>
```

### 댓글 작성 — 로그인 (Mock, 실제 저장 없음)

제출 시 `e.preventDefault()` + 입력값 초기화 (`setComment('')`).
저장 미지원 안내는 별도 표시 없음 (UI only임이 명확하므로).

### 댓글 empty state

댓글이 없을 때:
```tsx
<p className="text-gray-500 text-sm text-center py-6">작성된 댓글이 없습니다.</p>
```

---

## 7. 의존성

신규 패키지 없음. 기존 사용 중:
- `lucide-react` (ChevronLeft 아이콘)
- `react-router` (useLoaderData, redirect, Link)
- `~/shared/api/endpoints` (API_ENDPOINTS)
- `~/shared/api/server` (serverFetch)

---

## 8. 테스트 전략

브라우저 수동 검증 (기존 프로젝트 방식 동일):

| 시나리오 | 확인 항목 |
|----------|-----------|
| `/community/1` (비로그인) | 게시글 표시, 댓글 disabled |
| `/community/11` (비로그인) | "사용 불가" 화면 |
| `/community/1` (로그인) | 게시글 + 댓글 작성 활성 |
| `/community/999` | HTTP 404 응답 + 한글 에러 페이지 |
| "목록으로" 클릭 | `/community` 이동 |
| 로그인 버튼 클릭 | `/login?redirect=/community/11` 이동 확인 |
| meta title | `게시글 제목 \| 해독 AI` |
