import { redirect } from 'react-router';

import { LibraryDetailView } from '~/views/library/LibraryDetailView';

import { ApiError } from '~/shared/api/client';
import { API_ENDPOINTS } from '~/shared/api/endpoints';
import { serverFetch } from '~/shared/api/server';

import type { Route } from './+types/_protected.library.$id';
import type { BookResult } from '~/shared/types/translate';

export async function loader({ request, params }: Route.LoaderArgs) {
    try {
        const book = await serverFetch<BookResult>(
            request,
            API_ENDPOINTS.TRANSLATE_DETAIL(params.id),
        );
        return { book };
    } catch (err) {
        if (err instanceof Response) throw err;
        // 401 → 로그인 페이지로 (query 보존, _protected 병렬 실행으로 uncaught 방지)
        if (err instanceof ApiError && err.status === 401) {
            const { pathname, search } = new URL(request.url);
            throw redirect(`/login?redirect=${encodeURIComponent(`${pathname}${search}`)}`);
        }
        // 403/404 → 목록으로 이동 (존재하지 않거나 권한 없는 book)
        if (err instanceof ApiError && [403, 404].includes(err.status)) {
            throw redirect('/library');
        }
        throw err;
    }
}

export function meta({ data }: Route.MetaArgs) {
    const title = data?.book?.title ?? '번역 상세';
    return [{ title: `${title} | 해독 AI` }];
}

export default function LibraryDetailRoute() {
    return <LibraryDetailView />;
}
