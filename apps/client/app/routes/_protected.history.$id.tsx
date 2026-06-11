import { redirect } from 'react-router';

import { HistoryDetailView } from '~/views/history/HistoryDetailView';

import { ApiError } from '~/shared/api/client';
import { API_ENDPOINTS } from '~/shared/api/endpoints';
import { serverFetch } from '~/shared/api/server';

import type { Route } from './+types/_protected.history.$id';
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
        if (err instanceof ApiError && err.status === 401) {
            const { pathname, search } = new URL(request.url);
            throw redirect(`/login?redirect=${encodeURIComponent(`${pathname}${search}`)}`);
        }
        if (err instanceof ApiError && [403, 404].includes(err.status)) {
            throw redirect('/history');
        }
        throw err;
    }
}

export function meta({ data }: Route.MetaArgs) {
    const title = data?.book?.title ?? '번역 상세';
    return [{ title: `${title} | 해독 AI` }];
}

export default function HistoryDetailRoute() {
    return <HistoryDetailView />;
}
