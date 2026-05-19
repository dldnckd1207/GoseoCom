# 코딩 컨벤션 + 금지 규칙

---

## 파일/폴더 네이밍

- **컴포넌트:** PascalCase (`MyCard.tsx`, `NoticeTable.tsx`)
- **유틸/훅:** camelCase (`useMyList.ts`, `formatDate.ts`)
- **상수:** UPPER_SNAKE_CASE (`API_BASE_URL`)
- **타입 파일:** camelCase (`types.ts`, `index.ts`)

---

## Import 순서

```typescript
// 1. React / React Router (framework mode)
import { useState, useEffect } from 'react';
import { useNavigate, useLoaderData, useFetcher } from 'react-router';

// 2. Third-party
import { Loader2 } from 'lucide-react';
import { format } from 'date-fns';

// 3. Widgets
import { PageLayout } from '~/widgets/layout';

// 4. Features
import { useMyList } from '~/features/{domain}/hooks/useMyList';

// 5. Entities
import { userStore } from '~/entities/user';

// 6. Shared
import { Button } from '~/shared/ui/button';

// 7. Types (type-only imports, 항상 마지막)
import type { MyResponse } from '~/features/{domain}';
import type { Route } from './+types/my._index';
```

> **import alias:** React Router framework mode 프로젝트에서는 `~/`를 사용한다 (`@/` 아님). <br/>
> **Route 타입:** route 파일에서 loader/action/component args 타입은 `./+types/<routeName>` 자동 생성 타입을 사용한다 (`Route.LoaderArgs` / `Route.ActionArgs` / `Route.ComponentProps`).

---

## ESLint 설정 요점

React/Vite ESLint 설정과 동일하게 적용. 단, `routes/` 파일에만 default export 예외 추가 필요.

```js
// eslint.config.js
[
    // 전체: default export 금지
    { rules: { 'import/no-default-export': 'error' } },
    // routes/ 파일만 예외 (React Router framework mode가 route 컴포넌트에 default export 요구)
    {
        files: ['app/routes/**/*.tsx'],
        rules: { 'import/no-default-export': 'off' },
    },
]
```

> React Router framework mode는 `eslint-config-next` 같은 전용 config이 없으므로 React 기반 ESLint에 위 override만 추가한다.

---

## 컴포넌트 구조

```typescript
// 타입 정의
interface Props {
    data: MyResponse;
    onSelect: (id: string) => void;
}

// 컴포넌트
export function MyCard({ data, onSelect }: Props) {
    // hooks
    // handlers
    // render
}
```

---

## 타입 정의 규칙

```typescript
// API 요청 (조회): ~SearchRequest, ~DetailRequest
type MySearchRequest = PageRequest & { keyword?: string; };
type MyDetailRequest = { id: string; };

// API 요청 (CUD): ~CreateRequest, ~UpdateRequest, ~DeleteRequest
type MyCreateRequest = { name: string; };
type MyUpdateRequest = { id: string; name: string; };
type MyDeleteRequest = { id: string; };

// API 응답: ~Response 또는 ~DetailResponse
type MyResponse = { id: string; name: string; };

// 하위 타입: ~Item
type SubItem = { id: string; title: string; };

// Props: ~Props 또는 interface Props
interface MyCardProps { data: MyResponse; }
```

---

## Export 규칙

- **named export만 사용** — `export function MyComponent()`, `export function useMyList()`
- **default export 금지** — ESLint `import/no-default-export`로 강제
- **예외: `routes/` 하위 route 파일** — React Router framework mode가 route 컴포넌트에 default export를 요구하므로 허용
- **예외: loader/action** — `export async function loader()`, `export async function action()` named export 사용

```typescript
// ✅ routes/ 파일: default export 허용 (React Router framework mode 요구사항)
export async function loader() { ... }
export async function action() { ... }
export default function MyRoute() { return <MyView />; }

// ✅ 그 외 모든 파일: named export
export function MyView() { ... }
export function useMyList() { ... }
```

---

## 이벤트 핸들러 네이밍

| 위치 | 접두사 | 예시 |
|------|--------|------|
| Hook/컴포넌트 내부 정의 | `handle~` | `handleSearch`, `handleDelete`, `handleSubmit` |
| Props로 전달 | `on~` | `onSearch`, `onDelete`, `onSelect` |

```typescript
// Hook 내부
const handleSearch = () => { ... };

// Props 정의
interface Props { onSearch: () => void; }

// View에서 연결
<MySearchForm onSearch={handleSearch} />
```

---

## 에러 처리 패턴

| 상황 | 처리 방식 |
|------|----------|
| loader 조회 실패 | ErrorBoundary로 자동 처리 또는 `throw data(...)` / `throw new Response(...)` |
| 클라이언트 조회 실패 | `console.error` + `setError` (StateDisplay로 표시) |
| action/useFetcher 뮤테이션 실패 | `toast.error()` |
| action/useFetcher 뮤테이션 성공 | `toast.success()` + `navigate(-1)` 또는 `redirect()` |
| 폼 유효성 검증 | Zod 스키마 → React Hook Form이 자동 처리 |

```typescript
// loader 에러 throw (ErrorBoundary가 처리)
import { data } from 'react-router';

export async function loader() {
    const result = await getMyList();
    if (!result) throw data({ message: '데이터 없음' }, { status: 404 });
    return { data: result };
}

// useFetcher 완료 후 처리
useEffect(() => {
    if (fetcher.state === 'idle' && fetcher.data?.success) {
        toast.success('처리되었습니다.');
        navigate(-1);
    }
    if (fetcher.state === 'idle' && fetcher.data?.error) {
        toast.error(fetcher.data.error);
    }
}, [fetcher.state, fetcher.data]);
```

---

## 폼 처리 규칙

| 폼 유형 | 방식 | 사용 시점 |
|---------|------|----------|
| **CUD 폼** (validation 필요) | React Hook Form + Zod + useFetcher | 생성/수정 폼 |
| **검색 폼** (단순 필터) | `useSearchParams` + `useNavigate` | 목록 검색 |
| **단순 입력** (필드 1~2개) | `useState` | 간단한 입력 |

```typescript
// CUD 폼: React Hook Form + Zod + useFetcher
const mySchema = z.object({ name: z.string().min(1, '필수') });
const form = useForm({ resolver: zodResolver(mySchema) });
const fetcher = useFetcher();
const handleSubmit = form.handleSubmit((data) => fetcher.submit(data, { method: 'post' }));

// 검색 폼: useSearchParams + useNavigate
const [searchParams] = useSearchParams();
const navigate = useNavigate();
const handleSearch = (keyword: string) => {
    const params = new URLSearchParams(searchParams);
    params.set('keyword', keyword);
    navigate(`?${params.toString()}`);
};
```

---

## 금지 규칙 (Anti-Patterns)

아래 패턴은 프로젝트에서 **사용하지 않습니다**. 발견하면 즉시 수정하세요.

### API 호출

| 금지 | 올바른 방식 | 이유 |
|------|-----------|------|
| View/컴포넌트에서 직접 API 호출 | loader/action 또는 Hook 내에서 공통 서비스 함수 사용 | 레이어 분리 위반 |
| `fetch` 직접 사용 | `apiClient` (shared/api/) 사용 | 공통 인증/에러 처리 누락 |
| 초기 데이터를 Hook으로 fetch | `loader` + `useLoaderData()` 사용 | React Router framework mode 데이터 흐름 위반, 워터폴 발생 |

### 상태 관리

| 금지 | 올바른 방식 | 이유 |
|------|-----------|------|
| 필터/페이징 상태를 `useState`만으로 관리 | URL `searchParams` + `useNavigate()` | 새로고침/뒤로가기/링크 공유 시 유지 |
| 필터/페이징 상태를 Zustand에 저장 | URL `searchParams`로 관리 | Zustand는 전역 상태(auth 등)만 |
| 서버 데이터를 Zustand에 저장 | loader + `useLoaderData()` | React Router framework mode가 자동으로 재검증 처리 |

### 프로젝트 구조

| 금지 | 올바른 방식 | 이유 |
|------|-----------|------|
| `routes/` 파일에 비즈니스 로직 | `views/` View 컴포넌트에 위임 | Route → View 위임 패턴 |
| `features/` 간 직접 import | `entities/` 또는 `shared/`를 통해서만 공유 | FSD 레이어 의존성 규칙 |
| `entities/` 간 직접 import | 각 entity는 독립적 | 도메인 간 결합 방지 |
| `shared/` → `features/`/`entities/` import | 순환 의존성 발생 | 단방향 의존 원칙 |

### 코딩 스타일

| 금지 | 올바른 방식 | 이유 |
|------|-----------|------|
| `fetch` 직접 import | `apiClient` 또는 공통 서비스 함수 (shared/api/) 사용 | 공통 인증/에러 처리 누락 |
| `any` 타입 사용 | 구체적 타입 또는 `unknown` | 타입 안전성 |
| `console.log`에 개인정보 출력 | 에러 로깅만, 개인정보 마스킹 | 보안 |
| dayjs 사용 | date-fns 4.x 사용 | 프로젝트 표준 라이브러리 |
| `@/` alias 사용 | `~/` alias 사용 | React Router framework mode 프로젝트 표준 |
