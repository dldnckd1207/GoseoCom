# 구현 패턴 템플릿

---

## 프로젝트 구조 상세

```
app/
├── routes/           # Remix 파일 기반 라우팅 (loader + action + UI 위임)
│   ├── _index.tsx              # / (홈)
│   ├── _layout.tsx             # 공통 레이아웃 (Header/Footer)
│   ├── _auth.tsx               # 인증 레이아웃 (로그인/회원가입)
│   ├── my._index.tsx           # /my (목록)
│   ├── my.$id.tsx              # /my/:id (상세)
│   ├── my.create.tsx           # /my/create (등록)
│   └── my.$id.edit.tsx         # /my/:id/edit (수정)
│
├── views/            # 페이지 뷰 컴포넌트 (Hook + Feature UI 조합)
│
├── widgets/          # 조합 UI (여러 페이지에서 공유)
│   ├── layout/       # Header, Footer, PageLayout
│   └── ...
│
├── features/         # 기능별 모듈
│
├── entities/         # 공유 도메인 모델 (여러 feature에서 사용하는 비즈니스 모델)
│
└── shared/           # 공통 모듈
    ├── api/          # fetch 클라이언트, 엔드포인트, 서비스 함수
    ├── types/        # 인프라성 공통 타입 (PageRequest 등)
    ├── stores/       # Zustand 스토어 (authStore 등)
    ├── hooks/        # 공통 훅
    ├── lib/          # 유틸리티
    ├── ui/           # shadcn/ui + 프로젝트 유틸리티
    ├── config/       # 설정
    └── styles/       # CSS
```

> **파일 라우팅 규칙 (React Router framework mode):** `.`은 `/`로, `$`는 동적 세그먼트로 변환된다.
> `my.$id.edit.tsx` → `/my/:id/edit`

### Entity 모듈 구조

> **entities = 여러 feature에서 공유하는 비즈니스 도메인 모델.** 인프라성 타입(PageRequest 등)은 shared에 남긴다.

```
entities/{domain}/
├── types.ts         # 도메인 타입 정의
├── api.ts           # API 함수 (선택)
├── store.ts         # Zustand 스토어 (선택)
└── index.ts         # 배럴 export
```

| Entity | 구성 | 용도 |
|--------|------|------|
| `user` | 타입 + store | 인증 상태, 사용자 정보 (여러 feature에서 공유) |
| `file` | 타입 + API | 파일 업로드/다운로드 (여러 feature에서 공유 시) |

> **승격 기준:** feature에서 만든 타입/API가 2개 이상의 feature에서 사용되면 entities로 승격을 검토한다.

### Feature 모듈 구조

> **[필수] API/Types 파일 구조 기준:**
> - 도메인 객체 1개 → 단일 파일 (`api.ts`, `types.ts`)
> - 도메인 객체 2개 이상 → 반드시 디렉토리 분리 (`api/{entity}.api.ts`, `types/{entity}.ts`)
> - 단일 파일(`api.ts`)에 여러 도메인 객체를 섞지 않는다

### Zustand 스토어

| 스토어 | 위치 | 용도 | 특징 |
|--------|------|------|------|
| `authStore` | `shared/stores/` | 로그인 상태, 사용자 정보 | login/logout/checkAuth 액션 |

> **규칙:** 전역 상태가 필요한 경우만 Zustand 사용. 서버 데이터는 loader로, UI 상태(필터, 페이징 등)는 URL searchParams로 관리한다.

---

## 1. 새 Feature 모듈 생성

```
features/{domain}/
├── api.ts           # API 함수 (작으면 단일 파일)
├── api/             # API 함수 (크면 디렉토리: {entity}.api.ts)
├── types.ts         # 타입 정의 (또는 types/ 디렉토리)
├── hooks/           # 클라이언트 UI 상태 훅 (URL params, fetcher 등)
│   └── use{Entity}List.ts
├── ui/              # View에서 추출한 도메인 전용 UI 컴포넌트
│   ├── {Entity}SearchForm.tsx
│   └── {Entity}List.tsx (또는 Grid, Cards 등)
├── constants.ts     # 상수 (선택)
├── utils/           # 유틸리티 (선택)
└── index.ts         # 배럴 export
```

index.ts 패턴:
```typescript
export * from './types';
export * as {domain}Api from './api';
export { {Entity}SearchForm } from './ui/{Entity}SearchForm';
export { {Entity}List } from './ui/{Entity}List';
```

---

## 2. 새 API 연동 플로우

> **HTTP 클라이언트:** fetch API 기반. 공통 래퍼(`shared/api/`)를 통해 인증, 에러 처리, 응답 추출을 통일한다.

```
1. shared/api/endpoints.ts              → API_ENDPOINTS에 엔드포인트 상수 등록
2. features/{domain}/api.ts             → 공통 서비스 함수 활용하여 API 함수 작성
3. features/{domain}/types.ts           → 요청/응답 타입 정의
4. routes/{path}.tsx                    → loader/action에서 API 함수 직접 호출
5. features/{domain}/ui/                → View에서 분리할 UI 컴포넌트 작성
6. features/{domain}/index.ts           → 배럴 export (types + api + ui 컴포넌트)
```

> **Mock 데이터:** Backend 미구현 시 `features/{domain}/api.ts` 내에서 임시 mock을 작성하고, 구현 완료 후 제거.

API 함수 작성 패턴:
```typescript
import { API_ENDPOINTS } from '~/shared/api/endpoints';
import { fetchList, fetchDetail, fetchCreate, fetchUpdate, fetchDelete } from '~/shared/api/service.api';

import type { MyResponse, MySearchRequest, MyCreateRequest, MyUpdateRequest, MyDeleteRequest } from './types';
import type { PageData } from '~/shared/types/api';

export async function getMyList(params?: MySearchRequest): Promise<PageData<MyResponse>> {
    return fetchList<MyResponse, MySearchRequest>(API_ENDPOINTS.MY_LIST, params);
}

export async function getMyDetail(id: string): Promise<MyDetailResponse> {
    return fetchDetail<MyDetailResponse>(API_ENDPOINTS.MY_DETAIL, id);
}

export async function createMy(data: MyCreateRequest): Promise<MyResponse> {
    return fetchCreate<MyResponse, MyCreateRequest>(API_ENDPOINTS.MY_CREATE, data);
}

export async function updateMy(data: MyUpdateRequest): Promise<MyResponse> {
    return fetchUpdate<MyResponse, MyUpdateRequest>(API_ENDPOINTS.MY_UPDATE, data);
}

export async function deleteMy(data: MyDeleteRequest): Promise<void> {
    return fetchDelete<MyDeleteRequest>(API_ENDPOINTS.MY_DELETE, data);
}
```

공통 서비스 함수 선택 기준:

| 구분 | 함수 | HTTP Method | 용도 | 반환 타입 |
|------|------|-------------|------|----------|
| 조회 | `fetchList` | GET | 페이징 목록 조회 | `PageData<T>` |
| 조회 | `fetchDetail` | GET | 단건 조회 (id 전달) | `T` |
| 생성 | `fetchCreate` | POST | 신규 생성 | `T` |
| 수정 | `fetchUpdate` | PUT | 기존 데이터 수정 | `T` |
| 삭제 | `fetchDelete` | DELETE | 삭제 | `void` |

---

## 3. 타입 정의 패턴

```typescript
import type { PageRequest } from '~/shared/types/api';

// 목록 응답 → ~Response 접미사
type MyResponse = { id: string; name: string; ... };

// 검색 요청 → ~SearchRequest (PageRequest 확장)
type MySearchRequest = PageRequest & { keyword?: string; ... };

// 상세 응답 → ~DetailResponse 접미사
type MyDetailResponse = { id: string; ... };

// 생성 요청 → ~CreateRequest 접미사
type MyCreateRequest = { name: string; ... };

// 수정 요청 → ~UpdateRequest 접미사
type MyUpdateRequest = { id: string; name: string; ... };

// 삭제 요청 → ~DeleteRequest 접미사
type MyDeleteRequest = { id: string; };

// 파일 하단에 export 모아서
export type { MyResponse, MySearchRequest, MyDetailResponse, MyCreateRequest, MyUpdateRequest, MyDeleteRequest };
```

---

## 4. loader / action 패턴

> **React Router framework mode 데이터 흐름의 핵심.** 서버 데이터 조회는 `loader`, 뮤테이션은 `action`으로 처리한다.

### loader — 서버 데이터 로딩

```typescript
// routes/my._index.tsx
import { MyView } from '~/views/my/MyView';
import { getMyList } from '~/features/my/api';

import type { Route } from './+types/my._index';

export async function loader({ request }: Route.LoaderArgs) {
    const url = new URL(request.url);
    const page = Number(url.searchParams.get('page') ?? '1');
    const keyword = url.searchParams.get('keyword') ?? '';

    const data = await getMyList({ page, size: 10, keyword: keyword || undefined });
    return { data };
}

export default function MyRoute() {
    return <MyView />;
}
```

> **반환 패턴:**
> - 정상 응답: plain object를 그대로 `return` (직렬화는 프레임워크가 담당)
> - status/headers 지정 필요 시: `import { data } from 'react-router'` → `return data(value, { status, headers })`
> - `json()` 유틸은 사용하지 않는다 (v7에서 deprecated)

### action — 뮤테이션 처리

```typescript
// routes/my._index.tsx (이어서)
import { data, redirect } from 'react-router';

import { deleteMy } from '~/features/my/api';

import type { Route } from './+types/my._index';

export async function action({ request }: Route.ActionArgs) {
    const formData = await request.formData();
    const intent = String(formData.get('intent'));

    if (intent === 'delete') {
        const id = String(formData.get('id'));
        await deleteMy({ id });
        return { success: true };
    }

    return data({ error: 'Unknown intent' }, { status: 400 });
}
```

### View에서 loader 데이터 소비

```typescript
// views/my/MyView.tsx
import { useLoaderData } from 'react-router';

import type { loader } from '~/routes/my._index';

export function MyView() {
    const { data } = useLoaderData<typeof loader>();
    // ...
}
```

> **Route 타입 생성:** `Route.LoaderArgs`, `Route.ActionArgs`, `Route.ComponentProps`는 파일 경로 기반으로 `./+types/<routeName>`에서 자동 생성된다(`react-router typegen`). default export 컴포넌트에서 `loaderData`, `actionData`, `params`를 타입 안전하게 props로 받을 수도 있다.

---

## 5. Hook 작성 패턴

> **React Router framework mode에서 Hook의 역할:** 서버 데이터(초기 로딩)는 loader가 담당한다. Hook은 **URL searchParams 조작, useFetcher 기반 뮤테이션, 클라이언트 UI 상태** 관리에 집중한다.

### 목록 Hook — URL searchParams 패턴

```typescript
import { useNavigate, useSearchParams, useFetcher } from 'react-router';
import { toast } from 'sonner';

export function useMyList() {
    const [searchParams] = useSearchParams();
    const navigate = useNavigate();
    const fetcher = useFetcher();

    const currentPage = Number(searchParams.get('page') ?? '1');
    const searchKeyword = searchParams.get('keyword') ?? '';

    // 검색 — URL 변경으로 loader 재실행
    const handleSearch = (keyword: string) => {
        const params = new URLSearchParams(searchParams);
        params.set('keyword', keyword);
        params.set('page', '1');
        navigate(`?${params.toString()}`);
    };

    const handlePageChange = (page: number) => {
        const params = new URLSearchParams(searchParams);
        params.set('page', String(page));
        navigate(`?${params.toString()}`);
    };

    // 삭제 — useFetcher로 action 호출
    const handleDelete = (id: string) => {
        if (!confirm('삭제하시겠습니까?')) return;
        fetcher.submit(
            { intent: 'delete', id },
            { method: 'post' },
        );
    };

    const isDeleting = fetcher.state !== 'idle';

    return {
        searchKeyword,
        currentPage,
        handleSearch,
        handlePageChange,
        handleDelete,
        isDeleting,
    };
}
```

### CUD 폼 Hook 패턴

> 초기 데이터는 loader → `useLoaderData()`로 이미 받아온다. Hook은 **폼 상태 + useFetcher 제출**만 담당한다.

```typescript
import { useEffect } from 'react';
import { useNavigate, useFetcher } from 'react-router';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

const myFormSchema = z.object({
    name: z.string().min(1, '이름을 입력해주세요'),
    description: z.string().optional(),
});

type MyFormData = z.infer<typeof myFormSchema>;

export function useMyForm(defaultValues?: Partial<MyFormData>) {
    const navigate = useNavigate();
    const fetcher = useFetcher();

    const form = useForm<MyFormData>({
        resolver: zodResolver(myFormSchema),
        defaultValues: { name: '', description: '', ...defaultValues },
    });

    // fetcher 완료 후 처리
    useEffect(() => {
        if (fetcher.state === 'idle' && fetcher.data?.success) {
            navigate(-1);
        }
    }, [fetcher.state, fetcher.data, navigate]);

    const handleSubmit = form.handleSubmit((data) => {
        fetcher.submit(data, { method: 'post' });
    });

    return {
        form,
        handleSubmit,
        isSubmitting: fetcher.state !== 'idle',
    };
}
```

### Hook 패턴 선택 기준

| 패턴 | 방식 | 사용 시점 |
|------|------|----------|
| **초기 데이터 로딩** | `loader` + `useLoaderData()` | 페이지 진입 시 서버 데이터 |
| **목록 필터/페이징** | `useSearchParams` + `useNavigate` | URL 변경으로 loader 재실행 |
| **뮤테이션 (삭제/토글)** | `useFetcher` | 네비게이션 없는 서버 액션 |
| **폼 제출** | `useMyForm` (RHF + Zod + useFetcher) | 생성/수정 폼 |
| **클라이언트 전용 상태** | `useState` | 모달 open, 탭 선택 등 UI 상태 |

---

## 6. Route → View → Feature UI 3단계 패턴

```typescript
// routes/my._index.tsx — 라우팅 + 데이터 (loader/action + View 위임)
import { MyView } from '~/views/my/MyView';
import { getMyList } from '~/features/my/api';

import type { Route } from './+types/my._index';

export async function loader({ request }: Route.LoaderArgs) {
    const url = new URL(request.url);
    const page = Number(url.searchParams.get('page') ?? '1');
    const keyword = url.searchParams.get('keyword') ?? '';
    const data = await getMyList({ page, size: 10, keyword: keyword || undefined });
    return { data };
}

export default function MyRoute() {
    return <MyView />;
}
```

```typescript
// views/my/MyView.tsx — 조합 레이어 (50-80줄)
import { useLoaderData } from 'react-router';

import { MySearchForm, MyList } from '~/features/my';
import { useMyList } from '~/features/my/hooks/useMyList';
import { PaginationNav } from '~/shared/ui/pagination-nav';
import { PageLayout } from '~/widgets/layout';

import type { loader } from '~/routes/my._index';

export function MyView() {
    const { data } = useLoaderData<typeof loader>();
    const { searchKeyword, currentPage, handleSearch, handlePageChange, handleDelete } = useMyList();

    return (
        <PageLayout pageTitle="페이지 제목">
            <MySearchForm keyword={searchKeyword} onSearch={handleSearch} />
            <MyList
                items={data.items}
                total={data.total}
                onDelete={handleDelete}
            />
            <PaginationNav
                currentPage={currentPage}
                total={data.total}
                onPageChange={handlePageChange}
            />
        </PageLayout>
    );
}
```

```typescript
// features/my/ui/MySearchForm.tsx — 도메인 전용 UI (80-140줄)
import { Input } from '~/shared/ui/input';
import { Button } from '~/shared/ui/button';

interface Props { keyword: string; onSearch: (keyword: string) => void; }

export function MySearchForm({ keyword, onSearch }: Props) {
    return (
        <form role="search" onSubmit={(e) => { e.preventDefault(); onSearch(/* ... */); }}>
            <Input defaultValue={keyword} name="keyword" />
            <Button type="submit">검색</Button>
        </form>
    );
}
```

### 상세 Route/View 패턴

```typescript
// routes/my.$id.tsx
import { MyDetailView } from '~/views/my/MyDetailView';
import { getMyDetail } from '~/features/my/api';

import type { Route } from './+types/my.$id';

export async function loader({ params }: Route.LoaderArgs) {
    const detail = await getMyDetail(params.id!);
    return { detail };
}

export default function MyDetailRoute() {
    return <MyDetailView />;
}
```

```typescript
// views/my/MyDetailView.tsx
import { useLoaderData, useNavigate, useFetcher } from 'react-router';

import { PageLayout } from '~/widgets/layout';
import { Button } from '~/shared/ui/button';

import type { loader } from '~/routes/my.$id';

export function MyDetailView() {
    const { detail } = useLoaderData<typeof loader>();
    const navigate = useNavigate();
    const fetcher = useFetcher();

    const handleDelete = () => {
        if (!confirm('삭제하시겠습니까?')) return;
        fetcher.submit({ intent: 'delete', id: detail.id }, { method: 'post' });
    };

    return (
        <PageLayout pageTitle="상세">
            {/* 상세 내용 렌더링 */}
            <div className="flex gap-2">
                <Button onClick={() => navigate(`/my/${detail.id}/edit`)}>수정</Button>
                <Button variant="destructive" onClick={handleDelete}>삭제</Button>
                <Button variant="outline" onClick={() => navigate(-1)}>목록</Button>
            </div>
        </PageLayout>
    );
}
```

### 등록/수정 Route/View 패턴

```typescript
// routes/my.create.tsx
import { redirect } from 'react-router';

import { MyFormView } from '~/views/my/MyFormView';
import { createMy } from '~/features/my/api';

import type { Route } from './+types/my.create';

export async function action({ request }: Route.ActionArgs) {
    const formData = await request.formData();
    await createMy(Object.fromEntries(formData) as any);
    return redirect('/my');
}

export default function MyCreateRoute() {
    return <MyFormView />;
}
```

```typescript
// views/my/MyFormView.tsx
import { useMyForm } from '~/features/my/hooks/useMyForm';
import { Button } from '~/shared/ui/button';
import { Input } from '~/shared/ui/input';
import { PageLayout } from '~/widgets/layout';

interface Props { defaultValues?: { name?: string; description?: string }; isEdit?: boolean; }

export function MyFormView({ defaultValues, isEdit = false }: Props) {
    const { form, handleSubmit, isSubmitting } = useMyForm(defaultValues);
    const { register, formState: { errors } } = form;

    return (
        <PageLayout pageTitle={isEdit ? '수정' : '등록'}>
            <form onSubmit={handleSubmit}>
                <div>
                    <label htmlFor="name">이름</label>
                    <Input id="name" {...register('name')} />
                    {errors.name && <p className="text-red-500">{errors.name.message}</p>}
                </div>
                <div>
                    <label htmlFor="description">설명</label>
                    <Input id="description" {...register('description')} />
                </div>
                <div className="flex gap-2">
                    <Button type="submit" disabled={isSubmitting}>
                        {isEdit ? '수정' : '등록'}
                    </Button>
                    <Button type="button" variant="outline" onClick={() => history.back()}>
                        취소
                    </Button>
                </div>
            </form>
        </PageLayout>
    );
}
```

---

## 7. 레퍼런스 구현 (Golden Files)

새 기능을 구현할 때, `references/sample-board/` 안의 예시 파일을 **실제로 열어서 패턴을 따라** 작성하세요.

| 레이어 | 레퍼런스 파일 | 참조 포인트 |
|--------|-------------|------------|
| **엔드포인트** | `sample-board/shared/endpoints.ts` | `API_ENDPOINTS`에 상수 등록 |
| **타입 정의** | `sample-board/features/sample/types.ts` | `~Response`/`~SearchRequest`/`~CreateRequest`/`~UpdateRequest`/`~DeleteRequest` 접미사 |
| **API 함수** | `sample-board/features/sample/api.ts` | `fetchList`/`fetchDetail`/`fetchCreate`/`fetchUpdate`/`fetchDelete` 사용법 |
| **목록 Hook** | `sample-board/features/sample/hooks/useSampleList.ts` | useSearchParams + useNavigate + useFetcher |
| **폼 Hook** | `sample-board/features/sample/hooks/useSampleForm.ts` | RHF + Zod + useFetcher |
| **UI: 검색폼** | `sample-board/features/sample/ui/SampleSearchForm.tsx` | Props 수신, shared/ui 활용 |
| **UI: 목록** | `sample-board/features/sample/ui/SampleTable.tsx` | 데이터+핸들러 Props |
| **배럴 export** | `sample-board/features/sample/index.ts` | types + api + ui export |
| **View: 목록** | `sample-board/views/SampleView.tsx` | useLoaderData + Hook + Feature UI 조합 |
| **View: 상세** | `sample-board/views/SampleDetailView.tsx` | useLoaderData + useFetcher 삭제 |
| **View: 폼** | `sample-board/views/SampleFormView.tsx` | useMyForm + 등록/수정 분기 |
| **Route: 목록** | `sample-board/routes/sample._index.tsx` | loader + action(삭제) + ErrorBoundary + View 위임 |
| **Route: 상세** | `sample-board/routes/sample.$id.tsx` | loader(단건) + action(삭제) + ErrorBoundary + View 위임 |
| **Route: 등록** | `sample-board/routes/sample.create.tsx` | action(생성) + View 위임 |
| **Route: 수정** | `sample-board/routes/sample.$id.edit.tsx` | loader + action(수정) + defaultValues 주입 |

> **사용법:** `sample-board/features/sample/`의 구조를 복사하고 → 도메인명과 타입만 교체 <br />
> **UI 분리 기준:** View가 100줄을 넘으면 SearchForm, List/Grid를 `ui/`로 분리
