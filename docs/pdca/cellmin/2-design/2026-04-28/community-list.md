# Design — 커뮤니티 목록 페이지 (#98)

- **작성자:** cellmin
- **날짜:** 2026-04-28
- **Plan:** docs/pdca/cellmin/1-plan/2026-04-28/community-list.md

---

## 1. 아키텍처

공개 라우트 (`_layout` 하위). 별도 loader 없이 부모 `_layout.tsx`의 user 데이터를 `useRouteLoaderData`로 가져와 View에 prop으로 전달한다.

```
_layout.tsx (loader: user)
  └── _layout.community._index.tsx
        useRouteLoaderData('routes/_layout') → user
        └── CommunityListView({ user })
              useSearchParams() → tab, era, page
              Mock 데이터 필터 & 페이지네이션 (클라이언트)
```

---

## 2. 파일 구조

```
apps/client/app/
├── routes/
│   ├── _layout.community._index.tsx   # /community 목록 라우트
│   ├── _layout.community.$id.tsx      # /community/:id 스텁 (#99 구현 전까지)
│   └── _layout.community.write.tsx    # /community/write 스텁 (#100 구현 전까지)
├── views/community/
│   ├── CommunityListView.tsx           # 메인 뷰
│   └── mock.ts                         # Mock 게시글 데이터
└── shared/types/
    └── post.ts                         # Post 관련 타입
```

---

## 3. 타입 정의 (shared/types/post.ts)

```ts
export type PostTab = 'all' | 'translate' | 'question' | 'free'
export type PostEra = 'all' | 'prehistoric' | 'samguk' | 'goryeo' | 'joseon'

export type Post = {
    id: string
    title: string
    tab: Exclude<PostTab, 'all'>
    era: Exclude<PostEra, 'all'>
    author: string
    createdAt: string  // 'YYYY.MM.DD'
}
```

---

## 4. 라벨 매핑 (CommunityListView.tsx 내 상수)

```ts
const TAB_LABELS: Record<PostTab, string> = {
    all: '전체', translate: '번역', question: '질문', free: '자유',
}
const ERA_LABELS: Record<PostEra, string> = {
    all: '전체', prehistoric: '선사', samguk: '삼국', goryeo: '고려', joseon: '조선',
}
const TAB_KEYS = ['all', 'translate', 'question', 'free'] as const
const ERA_KEYS = ['all', 'prehistoric', 'samguk', 'goryeo', 'joseon'] as const
```

---

## 5. URL 쿼리스트링

| 파라미터 | 기본값 | 유효 값 |
|---------|--------|---------|
| `tab` | `all` | `all \| translate \| question \| free` |
| `era` | `all` | `all \| prehistoric \| samguk \| goryeo \| joseon` |
| `page` | `1` | 양의 정수 |

- `useSearchParams()` 로 읽기
- 필터 변경 시 `page`를 `1`로 리셋

### 파라미터 정규화 (parser helpers)

`URLSearchParams.get()`은 항상 `string | null`을 반환하므로 타입 가드와 fallback이 필요하다.

```ts
const parseTab = (value: string | null): PostTab =>
    TAB_KEYS.includes(value as PostTab) ? (value as PostTab) : 'all'

const parseEra = (value: string | null): PostEra =>
    ERA_KEYS.includes(value as PostEra) ? (value as PostEra) : 'all'

const parsePage = (value: string | null): number => {
    const parsed = Number(value)
    return Number.isInteger(parsed) && parsed > 0 ? parsed : 1
}
```

**replace 정책:** 아래 두 경우 모두 `setSearchParams(..., { replace: true })`로 URL을 정규화한다.
- `parseTab` / `parseEra` / `parsePage`에서 fallback이 발생한 경우 (`?tab=bad`, `?era=unknown`, `?page=abc` 등 유효하지 않은 값)
- `currentPage`가 `totalPages`를 초과해 보정된 경우 (`?page=999`)

공유 URL에 잘못된 파라미터가 남지 않도록 즉시 정규화한다.

---

## 6. 필터 & 페이지네이션 로직

```ts
const PAGE_SIZE = 10

// 1. 탭 필터
const byTab = tab === 'all' ? MOCK_POSTS : MOCK_POSTS.filter(p => p.tab === tab)

// 2. 시대 필터
const filtered = era === 'all' ? byTab : byTab.filter(p => p.era === era)

// 3. 페이지네이션
const totalPages = Math.ceil(filtered.length / PAGE_SIZE)
const currentPage = Math.min(Math.max(page, 1), totalPages || 1)
const paged = filtered.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE)
```

---

## 7. 글 작성하기 버튼

```ts
const handleWriteClick = () => {
    if (!user) {
        openModal({
            type: 'alert',
            message: '로그인이 필요한 서비스입니다.',
            buttons: [{ label: '확인', onClick: () => navigate('/login?redirect=/community/write') }],
        })
        return
    }
    navigate('/community/write')
}
```

---

## 8. 라우트 파일 (routes/_layout.community._index.tsx)

```tsx
import { useRouteLoaderData } from 'react-router'
import { CommunityListView } from '~/views/community/CommunityListView'
import type { loader as layoutLoader } from './_layout'
import type { Route } from './+types/_layout.community._index'

export function meta(_: Route.MetaArgs) {
    return [{ title: '커뮤니티 | 해독 AI' }]
}

export default function CommunityRoute() {
    const layoutData = useRouteLoaderData<typeof layoutLoader>('routes/_layout')
    const user = layoutData?.user ?? null
    return <CommunityListView user={user} />
}
```

---

## 9. Mock 데이터 (views/community/mock.ts)

총 30개 — 3페이지 버튼 표시 검증 가능 (`PAGE_SIZE=10`, 3페이지).
탭/시대 조합을 고르게 분산하여 필터 동작 확인 가능하도록 구성.

---

## 10. 테스트 전략

- TypeScript 타입 체크 (`npm run typecheck`)
- 브라우저 수동 검증:
  - 탭/시대 필터 변경 → URL 업데이트 확인
  - 새로고침 → 필터 유지 확인
  - 페이지 이동 → URL `page=` 변경 확인
  - 비로그인 글 작성하기 → 모달 확인
  - 로그인 글 작성하기 → `/community/write` 이동 확인
