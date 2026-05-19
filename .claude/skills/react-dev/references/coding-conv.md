# 코딩 컨벤션 + 금지 규칙

---

## 파일/폴더 네이밍

- **폴더:** kebab-case (`access-stats/`, `ai-chat/`)
- **컴포넌트:** PascalCase (`MyCard.tsx`, `MyTable.tsx`)
- **Page:** PascalCase + Page 접미사 (`MyListPage.tsx`, `MyDetailPage.tsx`)
- **훅:** camelCase + use 접두사 (`useMyList.ts`, `useMyForm.ts`)
- **API 파일:** camelCase (`myApi.ts`, `boardApi.ts`)
- **유틸:** camelCase (`formatDate.ts`, `transform.ts`)
- **타입 파일:** camelCase (`index.ts` 내 export)
- **상수:** UPPER_SNAKE_CASE (`API_BASE_URL`)

---

## Import 순서

```typescript
// 1. React + React Router
import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';

// 2. Third-party
import { useQuery, useMutation } from '@tanstack/react-query';
import { toast } from 'sonner';

// 3. Shared
import { Button } from '@/shared/ui/button';
import { usePagination } from '@/shared/hooks';
import { queryKeys } from '@/shared/lib/queryKeys';

// 4. Features + Entities
import { useMyList } from '@/features/my/hooks';
import { MyFilter, MyTable } from '@/features/my/components';
import { userStore } from '@/entities/user';

// 5. Types (type-only imports, 항상 마지막)
import type { MyResponse } from '@/features/my/types';
```

> **ESLint 자동 정렬:** `simple-import-sort` 플러그인으로 강제됨 (`eslint.config.js` 참조)

---

## 컴포넌트 내부 코드 순서

```typescript
export function MyListPage() {
    // 1. Hooks (useParams, useNavigate, usePagination 등)
    // 2. State (useState)
    // 3. Query (useQuery, useMutation)
    // 4. Derived (계산된 값)
    // 5. Effects (useEffect)
    // 6. Handlers (handleSearch, handleDelete 등)
    // 7. Early returns (로딩, 에러, 빈 상태)
    // 8. JSX return
}
```

---

## 타입 정의 규칙

```typescript
// API 요청: ~Request
interface MyCreateRequest { name: string; description?: string; }
interface MyUpdateRequest { id: string; name: string; description?: string; }

// API 응답: ~Response 또는 ~Detail
interface MyResponse { id: string; name: string; createdAt: string; }
interface MyDetail { id: string; name: string; description: string; createdAt: string; updatedAt: string; }

// 검색 조건: ~SearchParams
interface MySearchParams { keyword?: string; category?: string; }

// 폼 데이터: ~FormData
interface MyFormData { name: string; description: string; category: string; }

// Props: ~Props
interface MyTableProps { data: MyResponse[]; isLoading: boolean; }
```

---

## Export 규칙

- **named export만 사용** — `export function MyComponent()`
- **default export 금지** — `app/` 엔트리 파일만 예외
- **lazy import 패턴:** `React.lazy(() => import('./MyPage').then((m) => ({ default: m.MyPage })))`

### Barrel export 주의사항

```typescript
// features/[domain]/index.ts — 컴포넌트 + 타입만 export (권장)
export * from './components';
export * from './types';
// hooks와 api는 barrel에서 제외 — pages에서 직접 경로 import
// import { useMyList } from '@/features/my/hooks';
```

> hooks/api를 barrel에 포함하면 features 간 금지 규칙이 우회되기 쉽다.

---

## 이벤트 핸들러 네이밍

| 위치 | 접두사 | 예시 |
|------|--------|------|
| Hook/Page 내부 정의 | `handle~` | `handleSearch`, `handleDelete`, `handleSubmit` |
| Props로 전달 | `on~` | `onSearch`, `onChange`, `onSelect` |

---

## 금지 규칙 (Anti-Patterns)

### API 호출

| 금지 | 올바른 방식 | 이유 |
|------|-----------|------|
| Page/컴포넌트에서 직접 API 호출 | TanStack Query hooks 경유 | 캐시/에러 처리 통일 |
| `fetch` 직접 사용 | `apiClient` (shared/api/) 사용 | 공통 인증/에러 처리 누락 |
| QS 필요한 조회에 GET 사용 | 조회/생성 POST, 수정 PUT, 삭제 DELETE (GET은 QS 불필요한 단건만 허용) | QS 노출 방지, 보안 강화 |

### 상태 관리

| 금지 | 올바른 방식 | 이유 |
|------|-----------|------|
| 서버 데이터를 Zustand에 저장 | TanStack Query로 관리 | 캐시 무효화, 재조회 자동 처리 |
| Zustand store 간 양방향 참조 | 단방향 또는 독립 유지 (store→store 참조 1개 이하 권장) | 순환 의존 방지 |
| Page에 비즈니스 로직 | Features/Hooks에 위임 | FSD 레이어 분리 |
| features 간 Hook/Component/API import | shared 또는 entities를 통해 공유 | 의존성 규칙 (타입/상수만 허용, ESLint `no-restricted-imports` 강제 권장) |

### 코딩 스타일

| 금지 | 올바른 방식 | 이유 |
|------|-----------|------|
| `any` 타입 사용 | 구체적 타입 또는 `unknown` | 타입 안전성 (ESLint warn) |
| `console.log` 남용 | `console.warn`/`console.error`만 | ESLint `no-console` 규칙 |
| dayjs 사용 | date-fns 사용 | 프로젝트 표준 라이브러리 |
| `default export` | `named export` | lazy import 호환성 + 일관성 |

---

## Layout CSS 유틸리티 (`src/styles/layout.css`)

> **원칙:** 시맨틱 클래스를 우선 사용. 인라인 Tailwind는 일회성 미세 조정에만.
> **등록 기준:** 2개 이상 페이지에서 동일 클래스 조합이 반복되면 시맨틱 클래스로 등록.

| 카테고리 | 주요 클래스 | 용도 |
|----------|-----------|------|
| 레이아웃 | `layout-root`, `layout-body`, `layout-main`, `layout-content` | 앱 골격 |
| 사이드바 | `sidebar-main`, `sidebar-sub`, `sidebar-*-item`, `*-active`, `*-inactive` | 네비게이션 |
| 페이지 | `content-wrapper`, `list-header`, `list-count`, `filter-row`, `page-title` | 페이지 공통 |
| 그리드 | `grid-cards`, `grid-dashboard`, `grid-stats`, `grid-info` | 반응형 그리드 |
| 폼 | `form-grid`, `form-row`, `form-table-label`, `form-table-value` | 폼 레이아웃 |
| 테이블 | `table-container`, `table-header-row`, `table-row-clickable`, `th-center`, `td-center` | 테이블 |
| 버튼 | `btn-group-search`, `btn-toolbar`, `detail-actions` | 버튼 그룹 |
| 상태 | `empty-state`, `error-state` | 빈/에러 상태 |
| 유틸리티 | `flex-center`, `flex-between`, `flex-end` | 플렉스 단축 |

> **전체 클래스 목록은 `src/styles/layout.css` 원본 참조.**
> `@layer components {}` 사용 금지. `@apply`로 직접 정의.

---

## 접근성 필수 사항

| 요소 | 규칙 | 예시 |
|------|------|------|
| 아이콘 버튼 | `aria-label` 필수 | `<Button size="icon" aria-label="삭제">` |
| 테이블 클릭 행 | `tabIndex={0}` + `onKeyDown` | Enter/Space로 행 클릭 + `table-row-clickable` |
| 폼 요소 | `label` 연결 | `<Label htmlFor="id">` + `<Input id="id">` |
| 에러 메시지 | `aria-describedby` + `role="alert"` | 스크린리더 즉시 알림 |
| 이미지 | 정보성 `alt` 필수, 장식 `alt=""` + `aria-hidden` | 접근성 |
| 페이지 제목 | `PageTitle`이 `id="page-title"` 렌더링 → `<section aria-labelledby="page-title">` 연결 | 스크린리더 구조 파악 |
