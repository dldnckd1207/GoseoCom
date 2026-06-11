import { redirect } from 'react-router';

import { LibraryView } from '~/views/library/LibraryView';

import { API_ENDPOINTS } from '~/shared/api/endpoints';
import { serverFetch } from '~/shared/api/server';

import type { Route } from './+types/_layout.library._index';
import type { PageResult } from '~/shared/types/post';
import type { BookPublicListItem } from '~/shared/types/translate';

function parsePage(value: string | null): number {
    const n = Number(value);
    return Number.isInteger(n) && n > 0 ? n : 1;
}

export async function loader({ request }: Route.LoaderArgs) {
    const url = new URL(request.url);
    const page = parsePage(url.searchParams.get('page'));
    const q = (url.searchParams.get('q') ?? '').trim();
    const bm = url.searchParams.get('bm') === '1';

    const body: Record<string, unknown> = { page, size: 12 };
    if (q) body.q = q;
    if (bm) body.bm = true;

    try {
        const data = await serverFetch<PageResult<BookPublicListItem>>(
            request,
            API_ENDPOINTS.TRANSLATE_PUBLIC_LIST,
            { method: 'POST', body: JSON.stringify(body) },
            { auth: 'optional' },
        );
        const totalPages = Math.ceil(data.total / data.size) || 1;
        if (data.total > 0 && page > totalPages) {
            throw redirect(`/library?page=${totalPages}`);
        }
        return { items: data.items, total: data.total, page: data.page, size: data.size, q, bm, error: null };
    } catch (err) {
        if (err instanceof Response) throw err;
        return { items: [], total: 0, page: 1, size: 12, q, bm, error: '라이브러리를 불러오지 못했습니다.' };
    }
}

export function meta(_: Route.MetaArgs) {
    return [{ title: '라이브러리 | 해독 AI' }];
}

export default function LibraryRoute() {
    return <LibraryView />;
}
