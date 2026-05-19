import { API_ENDPOINTS } from './endpoints';

// SSR(server.ts)은 자체 BASE_URL 사용. 여기는 브라우저 클라이언트 전용.
// VITE_PUBLIC_API_URL: 브라우저가 접근 가능한 공개 URL (nginx 경유 도메인)
// dev: VITE_API_BASE_URL fallback (http://localhost:8000)
export const BASE_URL = import.meta.env.VITE_PUBLIC_API_URL ?? import.meta.env.VITE_API_BASE_URL ?? '';
export const PUBLIC_BASE_URL = BASE_URL;

export interface ApiWrappedResponse<T> {
    header: { success: boolean; code: string; message: string };
    body: { data: T | null };
}

export class ApiError extends Error {
    constructor(
        public code: string,
        message: string,
        public status: number,
    ) {
        super(message);
        this.name = 'ApiError';
    }
}

function extractData<T>(json: ApiWrappedResponse<T>, status: number): T {
    if (!json.header.success) {
        throw new ApiError(json.header.code, json.header.message, status);
    }
    return json.body.data as T;
}

// 동시 다중 401 요청 시 refresh를 한 번만 수행하기 위한 플래그
let isRefreshing = false;
let refreshPromise: Promise<void> | null = null;

async function tryRefresh(): Promise<void> {
    if (isRefreshing) return refreshPromise!;
    isRefreshing = true;
    refreshPromise = fetch(`${BASE_URL}${API_ENDPOINTS.AUTH_REFRESH}`, {
        method: 'POST',
        credentials: 'include',
    }).then((res) => {
        if (!res.ok) throw new ApiError('TOKEN_EXPIRED', '세션이 만료되었습니다.', res.status);
    }).finally(() => {
        isRefreshing = false;
        refreshPromise = null;
    });
    return refreshPromise;
}

function buildHeaders(options?: RequestInit): HeadersInit {
    return { 'Content-Type': 'application/json', ...options?.headers };
}

// 401 발생 시 refresh 시도 후 원 요청 1회 재전송. refresh 실패 시 /login redirect.
async function request<T>(path: string, options?: RequestInit): Promise<T> {
    const res = await fetch(`${BASE_URL}${path}`, {
        ...options,
        credentials: 'include',
        headers: buildHeaders(options),
    });

    if (res.status === 0 || res.status >= 502) {
        throw new ApiError('NETWORK_ERROR', '서버에 연결할 수 없습니다.', res.status);
    }

    if (res.status === 401) {
        await tryRefresh();
        const retryRes = await fetch(`${BASE_URL}${path}`, {
            ...options,
            credentials: 'include',
            headers: buildHeaders(options),
        });
        if (!retryRes.ok) {
            if (typeof window !== 'undefined') window.location.href = '/login';
            throw new ApiError('UNAUTHORIZED', '로그인이 필요합니다.', 401);
        }
        const retryJson: ApiWrappedResponse<T> = await retryRes.json();
        return extractData(retryJson, retryRes.status);
    }

    const json: ApiWrappedResponse<T> = await res.json();
    return extractData(json, res.status);
}

export const apiClient = {
    get:    <T>(path: string) =>
        request<T>(path, { method: 'GET' }),
    post:   <T>(path: string, body?: unknown) =>
        request<T>(path, { method: 'POST', body: JSON.stringify(body ?? {}) }),
    put:    <T>(path: string, body: unknown) =>
        request<T>(path, { method: 'PUT', body: JSON.stringify(body) }),
    delete: <T>(path: string, body?: unknown) =>
        request<T>(path, { method: 'DELETE', body: JSON.stringify(body ?? {}) }),
};
