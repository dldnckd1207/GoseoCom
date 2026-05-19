# API 컨벤션

---

## 핵심 규칙

- **HTTP Method:**
  - 생성/조회: `POST`
  - 수정: `PUT`
  - 삭제: `DELETE`
  - `GET`은 **QS(Query String)가 필요 없는 경우에 한해 허용** (경로 파라미터만으로 충분한 단건 조회, 파일 서빙 등)
  - `PATCH` 미사용
- 응답은 2단계 래핑: `{ header, body: { data: T } }` → `extractData()`로 추출
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
  "header": {
    "success": true,
    "code": "SUCCESS",
    "message": "요청이 성공적으로 처리되었습니다."
  },
  "body": {
    "data": { ... }
  }
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
  "header": {
    "success": false,
    "code": "POST_NOT_FOUND",
    "message": "게시글을 찾을 수 없습니다."
  },
  "body": {
    "data": null
  }
}
```

### 페이징 응답 형식

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

## shared/api/ 구성

```
shared/api/
├── client.ts        # fetch 래퍼 (JWT 쿠키 자동 첨부, extractData, 에러 처리)
├── endpoints.ts     # API_ENDPOINTS 상수
└── service.api.ts   # 공통 서비스 함수 (fetchList, fetchDetail, fetchCreate, fetchUpdate, fetchDelete)
```

### client.ts — fetch 래퍼

```typescript
// shared/api/client.ts
const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '';

// ── 타입 ──────────────────────────────────────────────
export interface ApiWrappedResponse<T> {
    header: { success: boolean; code: string; message: string };
    body: { data: T | null };
}

export class ApiError extends Error {
    constructor(
        public code: string,
        public message: string,
        public status: number,
    ) {
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
        credentials: 'include',   // JWT httpOnly 쿠키 자동 전송
        headers: {
            'Content-Type': 'application/json',
            ...options?.headers,
        },
    });

    // 네트워크/서버 다운 등 HTTP 레벨 오류 — JSON 파싱 불가 케이스
    if (res.status === 0 || res.status >= 502) {
        throw new ApiError('NETWORK_ERROR', '서버에 연결할 수 없습니다.', res.status);
    }

    // 앱 내부 Exception — 글로벌 핸들러가 항상 { header, body } 포맷으로 래핑
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

### service.api.ts — 공통 서비스 함수

```typescript
import { apiClient } from './client';
import type { PageData, PageRequest } from '~/shared/types/api';

// 목록 조회
export function fetchList<T, P extends PageRequest>(endpoint: string, params?: P): Promise<PageData<T>> {
    return apiClient.post<PageData<T>>(endpoint, params ?? {});
}

// 단건 조회
export function fetchDetail<T>(endpoint: string, id: string): Promise<T> {
    return apiClient.post<T>(endpoint, { id });
}

// 생성
export function fetchCreate<T, B>(endpoint: string, body: B): Promise<T> {
    return apiClient.post<T>(endpoint, body);
}

// 수정
export function fetchUpdate<T, B>(endpoint: string, body: B): Promise<T> {
    return apiClient.put<T>(endpoint, body);
}

// 삭제
export function fetchDelete(endpoint: string, id: string): Promise<void> {
    return apiClient.delete<void>(endpoint, { id });
}
```

---

## API 파일 배치 규칙

**판단 기준:** "이 API를 호출하는 곳이 여러 feature에 걸쳐 있는가?"

| 위치 | 대상 | 예시 |
|------|------|------|
| `entities/{domain}/api.ts` | 여러 feature에서 공유하는 도메인 API | user, file |
| `features/{domain}/api.ts` | 단일 feature 전용 API | translation, community, library |
| `shared/api/` | 인프라성 (클라이언트, 엔드포인트, 서비스 함수) | client.ts, endpoints.ts |

---

## 인증 방식 (JWT httpOnly 쿠키)

| 토큰 | 저장 위치 | 특징 |
|------|----------|------|
| Access Token | httpOnly 쿠키 | JS 접근 불가, XSS 방어 |
| Refresh Token | httpOnly 쿠키 | Rotation 방식 (1회용) |

> **클라이언트에서 토큰을 직접 다루지 않는다.** `credentials: 'include'`로 자동 전송.

---

## 에러 코드 체계

> `header.code`로 분기 처리. 프론트는 `ApiError.code`로 핸들링.

### 공통 에러 코드

| 코드 | 의미 | 프론트 처리 |
|------|------|-----------|
| `BAD_REQUEST` | 잘못된 요청 (범용) | toast 에러 메시지 |
| `INVALID_INPUT` | 입력값 오류 | 폼 필드별 에러 표시 |
| `UNAUTHORIZED` | 인증 필요 (토큰 없음) | 로그인 페이지 리다이렉트 |
| `TOKEN_EXPIRED` | 토큰 만료 | 로그인 페이지 리다이렉트 |
| `INVALID_TOKEN` | 토큰 형식 오류 | 로그인 페이지 리다이렉트 |
| `FORBIDDEN` | 권한 없음 | 권한 없음 안내 |
| `WITHDRAWN_USER` | 탈퇴 사용자 재가입 시도 | 안내 메시지 표시 |
| `NOT_FOUND` | 리소스 없음 | toast 또는 404 페이지 |
| `CONFLICT` | 리소스 충돌 | toast 에러 메시지 |
| `NETWORK_ERROR` | 서버 연결 실패 | toast + 재시도 유도 |
| `INTERNAL_ERROR` | 서버 내부 오류 | 일반 에러 toast |

### 비즈니스 에러 코드 (예시)

| 코드 | 의미 |
|------|------|
| `USER_NOT_FOUND` | 사용자 없음 |
| `POST_NOT_FOUND` | 게시글 없음 |
| `BOOK_NOT_FOUND` | 고서 없음 |
| `TRANSLATION_NOT_FOUND` | 번역 결과 없음 |
| `DUPLICATE_RESOURCE` | 중복 리소스 |
| `ACCESS_DENIED` | 접근 거부 |
| `LOGIN_REQUIRED` | 로그인 필요 |

---

## 에러 처리 패턴

```typescript
// loader에서 에러 처리
import { data, redirect } from 'react-router';

export async function loader() {
    try {
        const result = await getMyList();
        return { data: result };
    } catch (err) {
        if (err instanceof ApiError && err.code === 'UNAUTHORIZED') {
            throw redirect('/login');
        }
        throw data({ message: err instanceof ApiError ? err.message : '오류가 발생했습니다.' }, { status: 500 });
    }
}

// useFetcher/hook에서 에러 처리
catch (err) {
    const message = err instanceof ApiError ? err.message : '요청에 실패했습니다.';
    toast.error(message);
}
```
