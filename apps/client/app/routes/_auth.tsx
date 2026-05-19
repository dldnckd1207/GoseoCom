import { Outlet, redirect } from 'react-router';

import { ApiError } from '~/shared/api/client';
import { API_ENDPOINTS } from '~/shared/api/endpoints';
import { serverFetch } from '~/shared/api/server';
import { isSafeRedirect } from '~/shared/lib/redirect';

import type { Route } from './+types/_auth';
import type { User } from '~/shared/types/auth';

export async function loader({ request }: Route.LoaderArgs) {
    const url = new URL(request.url);
    const raw = url.searchParams.get('redirect') ?? '/';
    const redirectTo = isSafeRedirect(raw) ? raw : '/';

    try {
        // 로그인 상태이면 redirect (비로그인 전용 레이아웃)
        await serverFetch<User>(request, API_ENDPOINTS.ME, undefined, { auth: 'optional' });
        throw redirect(redirectTo);
    } catch (err) {
        if (err instanceof Response) throw err;
        // 미인증(401), 사용자 없음(404 — 스테일 토큰), 서버 미기동 → 로그인 페이지 그대로 렌더링
        if (err instanceof ApiError && (err.status === 401 || err.status === 404 || err.code === 'NETWORK_ERROR')) return null;
        if (err instanceof TypeError) return null;
        throw err;
    }
}

export default function AuthLayout() {
    return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50">
            <Outlet />
        </div>
    );
}
