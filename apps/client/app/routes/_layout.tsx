import { useEffect } from 'react';

import { Outlet, useLoaderData, useNavigate, useSearchParams } from 'react-router';

import { Footer, Header } from '~/widgets/layout';

import { API_ENDPOINTS } from '~/shared/api/endpoints';
import { serverFetch } from '~/shared/api/server';
import { REDIRECT_AFTER_LOGIN_KEY } from '~/shared/lib/redirect';
import { openModal } from '~/shared/ui/modal';

import type { Route } from './+types/_layout';
import type { User } from '~/shared/types/auth';

export async function loader({ request }: Route.LoaderArgs) {
    try {
        const user = await serverFetch<User>(request, API_ENDPOINTS.ME, undefined, { auth: 'optional' });
        return { user };
    } catch (err) {
        if (err instanceof Response) throw err;
        return { user: null };
    }
}

export default function RootLayoutRoute() {
    const { user } = useLoaderData<typeof loader>();
    const [searchParams] = useSearchParams();
    const navigate = useNavigate();

    useEffect(() => {
        // 1순위: 로그인 후 원래 URL 복귀 (sessionStorage)
        try {
            const redirectPath = sessionStorage.getItem(REDIRECT_AFTER_LOGIN_KEY);
            if (redirectPath) {
                sessionStorage.removeItem(REDIRECT_AFTER_LOGIN_KEY);
                navigate(redirectPath, { replace: true });
                return;
            }
        } catch {
            // sessionStorage 미지원 환경 — 무시
        }

        // 2순위: 로그아웃 알림
        if (searchParams.get('logout') === 'true') {
            openModal({
                type: 'alert',
                message: '로그아웃 되었습니다.',
                buttons: [{ label: '확인', onClick: () => navigate('/', { replace: true }) }],
            });
        }
    }, [searchParams, navigate]);

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
