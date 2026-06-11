import { redirect } from 'react-router';

import { ApiError } from './client';
import { API_ENDPOINTS } from './endpoints';

import type { ApiWrappedResponse } from './client';

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

const _MUTATING_METHODS = new Set(['POST', 'PUT', 'DELETE', 'PATCH']);

// double-submit CSRF: 전달받은 cookie 헤더에서 csrf_token을 추출 (보안 #7)
export function parseCsrfToken(cookie: string): string | undefined {
    const match = cookie.match(/(?:^|;\s*)csrf_token=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : undefined;
}

type ServerFetchAuthMode = 'required' | 'optional' | 'action';

export async function serverFetch<T>(
    request: Request,
    path: string,
    init?: RequestInit,
    options: { auth?: ServerFetchAuthMode } = {},
): Promise<T> {
    const { auth = 'required' } = options;
    const cookie = request.headers.get('cookie') ?? '';
    const method = (init?.method ?? 'GET').toUpperCase();
    const headers: Record<string, string> = {
        cookie,
        'Content-Type': 'application/json',
        ...(init?.headers as Record<string, string> | undefined),
    };
    const csrf = parseCsrfToken(cookie);
    if (csrf && _MUTATING_METHODS.has(method)) headers['X-CSRF-Token'] = csrf;
    const res = await fetch(`${BASE_URL}${path}`, { ...init, headers });

    if (res.status === 0 || res.status >= 502) {
        throw new ApiError('NETWORK_ERROR', '서버에 연결할 수 없습니다.', res.status);
    }

    if (res.status === 401) {
        // action: refresh 시도 없이 ApiError throw
        if (auth === 'action') {
            throw new ApiError('UNAUTHORIZED', '로그인이 필요합니다.', 401);
        }

        // optional/required: refresh 시도
        // - optional: 성공 시 현재 URL redirect, 실패 시 ApiError throw (user: null 처리)
        // - required: 성공 시 현재 URL redirect, 실패 시 /login redirect
        const url = new URL(request.url);
        const currentPath = `${url.pathname}${url.search}`;
        const loginRedirect = `/login?redirect=${encodeURIComponent(currentPath)}`;

        const hasRefreshToken = cookie.split(';').some((c) => c.trim().startsWith('refresh_token='));
        if (!hasRefreshToken) {
            if (auth === 'optional') throw new ApiError('UNAUTHORIZED', '로그인이 필요합니다.', 401);
            throw redirect(loginRedirect);
        }

        const refreshRes = await fetch(`${BASE_URL}${API_ENDPOINTS.AUTH_REFRESH}`, {
            method: 'POST',
            headers: { cookie },
        });

        if (!refreshRes.ok) {
            if (auth === 'optional') throw new ApiError('UNAUTHORIZED', '로그인이 필요합니다.', 401);
            throw redirect(loginRedirect);
        }

        // 다중 Set-Cookie 처리 (access_token + refresh_token)
        const setCookieHeaders = refreshRes.headers.getSetCookie?.() ?? [];
        if (setCookieHeaders.length === 0) {
            if (auth === 'optional') throw new ApiError('UNAUTHORIZED', '로그인이 필요합니다.', 401);
            throw redirect(loginRedirect);
        }

        const responseHeaders = new Headers({ Location: request.url });
        setCookieHeaders.forEach((value) => responseHeaders.append('Set-Cookie', value));
        throw new Response(null, { status: 302, headers: responseHeaders });
    }

    const json: ApiWrappedResponse<T> = await res.json();
    if (!json.header.success) {
        throw new ApiError(json.header.code, json.header.message, res.status);
    }
    return json.body.data as T;
}
