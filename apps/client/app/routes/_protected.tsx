import { useEffect } from 'react';

import { Outlet, useLoaderData, useNavigate } from 'react-router';

import { Footer, Header } from '~/widgets/layout';

import { ApiError } from '~/shared/api/client';
import { API_ENDPOINTS } from '~/shared/api/endpoints';
import { serverFetch } from '~/shared/api/server';
import { openModal } from '~/shared/ui/modal';

import type { Route } from './+types/_protected';
import type { User } from '~/shared/types/auth';

export async function loader({ request }: Route.LoaderArgs) {
    const { pathname, search } = new URL(request.url);
    const encodedPath = encodeURIComponent(`${pathname}${search}`);
    try {
        const user = await serverFetch<User>(request, API_ENDPOINTS.ME, undefined, { auth: 'required' });
        return { user, redirectTo: null };
    } catch (err) {
        if (err instanceof ApiError && err.status === 401)
            return { user: null, redirectTo: `/login?redirect=${encodedPath}` };
        if (err instanceof TypeError)
            return { user: null, redirectTo: `/login?redirect=${encodedPath}` };
        throw err;
    }
}

export default function ProtectedLayout() {
    const { user, redirectTo } = useLoaderData<typeof loader>();
    const navigate = useNavigate();

    useEffect(() => {
        if (!redirectTo) return;
        // throw redirect() 대신 모달 → navigate(replace)로 처리:
        // 1. 사용자에게 로그인 필요 안내 제공 (UX 개선)
        // 2. navigate({ replace: true })로 히스토리 교체 → 뒤로가기 트랩 방지
        openModal({
            type: 'alert',
            message: '로그인이 필요합니다.',
            showIcon: false,
            dismissible: false,
            buttons: [
                {
                    label: '확인',
                    variant: 'default',
                    onClick: () => navigate(redirectTo, { replace: true }),
                },
            ],
        });
    }, [redirectTo, navigate]);

    if (redirectTo) return null;

    return (
        <div className="min-h-screen flex flex-col bg-gray-50">
            <Header user={user} />
            <main className="flex-1">
                <Outlet />
            </main>
            <Footer />
        </div>
    );
}
