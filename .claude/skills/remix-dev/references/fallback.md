# Fallback + 에러 처리 전략

---

## 에러 처리 흐름

```
loader/action에서 throw
  → 해당 route의 ErrorBoundary가 catch
  → 없으면 부모 route로 버블링
  → 최상위 root ErrorBoundary까지 전파
```

> **원칙:** loader/action에서 복구 불가능한 에러는 `throw`한다. View에서 try/catch로 잡지 않는다.

---

## loader 에러 처리

### 기본 패턴

```typescript
// routes/my._index.tsx
import { data, redirect } from 'react-router';

import type { Route } from './+types/my._index';

export async function loader({ request }: Route.LoaderArgs) {
    try {
        const result = await getMyList();
        return { data: result };
    } catch (err) {
        if (err instanceof ApiError) {
            // 인증 만료 → 로그인 리다이렉트
            if (err.code === 'UNAUTHORIZED') {
                throw redirect('/login');
            }
            // 그 외 앱 에러 → ErrorBoundary로 전달
            throw data({ code: err.code, message: err.message }, { status: err.status });
        }
        // 네트워크/서버 다운
        throw data({ code: 'NETWORK_ERROR', message: '서버에 연결할 수 없습니다.' }, { status: 503 });
    }
}
```

> **반환 패턴:**
> - 정상 응답: plain object를 그대로 `return` (status 200)
> - status code 지정 필요 시: `return data(value, { status })`
> - 에러: `throw data(value, { status })` — ErrorBoundary로 전달
> - 리다이렉트: `throw redirect('/login')`

### ErrorBoundary

```typescript
// routes/my._index.tsx (이어서)
import { useRouteError, isRouteErrorResponse, Link } from 'react-router';

export function ErrorBoundary() {
    const error = useRouteError();

    if (isRouteErrorResponse(error)) {
        return (
            <div className="error-state">
                <p>{error.data?.message ?? '오류가 발생했습니다.'}</p>
                <Link to=".">다시 시도</Link>
            </div>
        );
    }

    return (
        <div className="error-state">
            <p>예상치 못한 오류가 발생했습니다.</p>
        </div>
    );
}
```

> **ErrorBoundary 배치 기준:**
> - 페이지 전체가 깨지면 안 되는 route → 해당 route에 선언
> - 공통 에러 처리 → `root.tsx`의 ErrorBoundary

---

## useFetcher 에러 처리

loader와 달리 useFetcher는 ErrorBoundary로 가지 않는다. `fetcher.data`로 직접 처리한다.

```typescript
// action에서 에러를 data()로 반환 (status code 필요 시)
import { data } from 'react-router';

import type { Route } from './+types/my._index';

export async function action({ request }: Route.ActionArgs) {
    try {
        await createMy(formData);
        return { success: true };
    } catch (err) {
        if (err instanceof ApiError) {
            return data({ success: false, code: err.code, message: err.message }, { status: err.status });
        }
        return data({ success: false, code: 'UNKNOWN', message: '처리 중 오류가 발생했습니다.' }, { status: 500 });
    }
}

// View/Hook에서 fetcher 결과 처리
useEffect(() => {
    if (fetcher.state === 'idle' && fetcher.data) {
        if (fetcher.data.success) {
            toast.success('처리되었습니다.');
            navigate(-1);
        } else {
            toast.error(fetcher.data.message ?? '오류가 발생했습니다.');
        }
    }
}, [fetcher.state, fetcher.data]);
```

---

## API 에러 코드별 처리

| 코드 | 처리 방식 |
|------|----------|
| `UNAUTHORIZED` | `redirect('/login')` |
| `FORBIDDEN` | 권한 없음 페이지 또는 toast |
| `NOT_FOUND` | 404 ErrorBoundary 또는 toast |
| `NETWORK_ERROR` | toast 안내 + 재시도 유도 |
| `INVALID_INPUT` | 폼 필드별 에러 메시지 표시 |
| 그 외 | toast 에러 메시지 |

---

## 빈 상태 (Empty State) 처리

loader는 성공했지만 데이터가 없는 경우 — ErrorBoundary가 아닌 View에서 처리한다.

```typescript
export function MyView() {
    const { data } = useLoaderData<typeof loader>();

    if (data.items.length === 0) {
        return (
            <PageLayout pageTitle="목록">
                <div className="empty-state">
                    <p>등록된 항목이 없습니다.</p>
                </div>
            </PageLayout>
        );
    }

    return ( /* 정상 렌더링 */ );
}
```

---

## 로딩 상태 처리

loader는 서버에서 실행 완료 후 페이지가 렌더링되므로 별도 로딩 스피너가 불필요하다.
단, `useFetcher`나 페이지 이동 중에는 `useNavigation`으로 처리한다.

```typescript
import { useNavigation } from 'react-router';

export function MyView() {
    const navigation = useNavigation();
    const isLoading = navigation.state === 'loading';

    return (
        <PageLayout pageTitle="목록">
            {isLoading && <div className="loading-overlay" />}
            {/* ... */}
        </PageLayout>
    );
}
```
