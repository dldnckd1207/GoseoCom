# API 컨벤션

---

## 핵심 규칙

- **HTTP Method:**
  - 생성/조회: `POST`
  - 수정: `PUT`
  - 삭제: `DELETE`
  - `GET`은 QS(Query String)가 필요 없는 경우에 한해 허용 (경로 파라미터만으로 충분한 단건 조회 등)
  - `PATCH` 미사용
- 응답은 2단계 래핑: `{ header, body: { data: T } }` → `extractData()`로 추출
- 모든 API 호출은 TanStack Query를 통해 수행
- 인증: JWT httpOnly 쿠키 자동 전송 (`credentials: 'include'`)

---

## Base URL

- **환경 변수:** `VITE_API_BASE_URL`
- **예시:** `http://localhost:8000`

---

## 공통 응답 형식

### 성공

```json
{
  "header": { "success": true, "code": "SUCCESS", "message": "..." },
  "body": { "data": { ... } }
}
```

### 작업별 code / HTTP 상태

| 작업 | code | HTTP |
|------|------|------|
| 조회 | `SUCCESS` | 200 |
| 생성 | `CREATED` | 201 |
| 수정 | `UPDATED` | 200 |
| 삭제 | `DELETED` | 200 |

### 실패

```json
{
  "header": { "success": false, "code": "NOT_FOUND", "message": "리소스를 찾을 수 없습니다." },
  "body": { "data": null }
}
```

### 페이징 응답

```typescript
// PageData<T> — body.data 안에 포함 (server-dev PageData와 동일)
type PageData<T> = {
    items: T[];
    total: number;
    page: number;
    size: number;
};
```

---

## shared/api/client.ts — fetch 래퍼

```typescript
const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '';

export interface ApiWrappedResponse<T> {
    header: { success: boolean; code: string; message: string };
    body: { data: T | null };
}

export class ApiError extends Error {
    constructor(public code: string, public message: string, public status: number) {
        super(message);
    }
}

// ── 응답 봉투 파싱 (SRP: 서버 계약 추출 전담) ──────────
function extractData<T>(json: ApiWrappedResponse<T>, status: number): T {
    if (!json.header.success) {
        throw new ApiError(json.header.code, json.header.message, status);
    }
    return json.body.data as T;
}

// ── HTTP 전송 (SRP: transport 전담) ───────────────────
async function request<T>(path: string, options?: RequestInit): Promise<T> {
    const res = await fetch(`${BASE_URL}${path}`, {
        ...options,
        credentials: 'include',
        headers: { 'Content-Type': 'application/json', ...options?.headers },
    });

    if (res.status === 0 || res.status >= 502) {
        throw new ApiError('NETWORK_ERROR', '서버에 연결할 수 없습니다.', res.status);
    }

    const json: ApiWrappedResponse<T> = await res.json();
    return extractData(json, res.status);
}

export const apiClient = {
    post:   <T>(path: string, body?: unknown) =>
        request<T>(path, { method: 'POST', body: JSON.stringify(body ?? {}) }),
    put:    <T>(path: string, body: unknown) =>
        request<T>(path, { method: 'PUT', body: JSON.stringify(body) }),
    delete: <T>(path: string, body?: unknown) =>
        request<T>(path, { method: 'DELETE', body: JSON.stringify(body ?? {}) }),
};
```

---

## QueryProvider 기본 설정

```typescript
// app/providers/QueryProvider.tsx
const queryClient = new QueryClient({
    defaultOptions: {
        queries: {
            staleTime: 5 * 60 * 1000,        // 5분 — 이 시간 내 재요청 시 캐시 사용
            gcTime: 30 * 60 * 1000,           // 30분 — 미사용 캐시 정리
            retry: 1,                          // 실패 시 1회 재시도
            refetchOnWindowFocus: false,       // 탭 전환 시 자동 재조회 비활성화
        },
    },
});
```

---

## Query Keys 패턴

```typescript
// shared/lib/queryKeys.ts
export const queryKeys = {
    sample: {
        all:    ['sample'] as const,
        list:   (params: SampleSearchParams) => ['sample', 'list', params] as const,
        detail: (id: string) => ['sample', 'detail', id] as const,
    },
};
```

> **규칙:** `invalidateQueries`는 `queryKeys.{domain}.all`로 해당 도메인 전체 캐시 무효화.

### queryKey 정규화 (stableParams)

```typescript
// shared/lib/stableParams.ts
export function stableParams<T extends Record<string, unknown>>(params: T): T {
    return Object.fromEntries(
        Object.entries(params)
            .filter(([, v]) => v !== undefined && v !== '')
            .sort(([a], [b]) => a.localeCompare(b))
    ) as T;
}

// 사용
queryKey: queryKeys.sample.list(stableParams(params)),
```

---

## 에러 처리 계층

| 계층 | 담당 | 처리 대상 |
|------|------|----------|
| **apiClient** (`shared/api/client.ts`) | 인프라 에러 | 네트워크 에러 → `NETWORK_ERROR` throw |
| **extractData** | 앱 에러 | `header.success === false` → `ApiError` throw |
| **Mutation onError** (각 Hook) | 비즈니스 에러 | `ApiError.message` toast |
| **Query isError** | 조회 에러 | UI에서 에러 상태 표시 |
| **PrivateRoute** | 인증 확인 | JWT 쿠키 유효성 검증, 만료 시 로그인 리다이렉트 |

```typescript
// Mutation onError — 비즈니스 에러 처리
useMutation({
    mutationFn: ...,
    onError: (err) => {
        const message = err instanceof ApiError ? err.message : '오류가 발생했습니다.';
        toast.error(message);
        if (err instanceof ApiError && err.code === 'UNAUTHORIZED') {
            navigate('/login');
        }
    },
});
```

### PrivateRoute — 인증 확인

```typescript
function PrivateRoute() {
    const bootstrapped = useRef(false);
    const [pageState, setPageState] = useState<'loading' | 'authenticated' | 'unauthenticated'>('loading');

    useEffect(() => {
        if (bootstrapped.current) return;
        bootstrapped.current = true;
        // JWT 쿠키 유효성 확인 API 호출
        // 성공 → 'authenticated', 실패(UNAUTHORIZED) → 'unauthenticated'
    }, []);

    if (pageState === 'loading') return <LoadingSpinner />;
    if (pageState === 'unauthenticated') return <Navigate to="/login" />;
    return <Outlet />;
}
```

---

## 에러 코드 체계

| 코드 | 의미 | 처리 |
|------|------|------|
| `BAD_REQUEST` | 잘못된 요청 (범용) | toast 에러 메시지 |
| `INVALID_INPUT` | 입력값 오류 | 폼 필드 에러 표시 |
| `UNAUTHORIZED` | 인증 필요 (토큰 없음) | 로그인 리다이렉트 |
| `TOKEN_EXPIRED` | 토큰 만료 | 로그인 리다이렉트 |
| `INVALID_TOKEN` | 토큰 형식 오류 | 로그인 리다이렉트 |
| `FORBIDDEN` | 권한 없음 | 권한 없음 안내 |
| `WITHDRAWN_USER` | 탈퇴 사용자 재가입 시도 | 안내 메시지 표시 |
| `NOT_FOUND` | 리소스 없음 | toast 또는 404 |
| `CONFLICT` | 중복 등 충돌 | toast |
| `NETWORK_ERROR` | 서버 연결 실패 | toast + 재시도 유도 |
| `INTERNAL_ERROR` | 서버 내부 오류 | 일반 에러 toast |
