import { HistoryView } from '~/views/history/HistoryView';

import { API_ENDPOINTS } from '~/shared/api/endpoints';
import { serverFetch } from '~/shared/api/server';

import type { Route } from './+types/_protected.history._index';
import type { PageResult } from '~/shared/types/post';
import type { BookListItem, BookStatus } from '~/shared/types/translate';

const TAB_STATUS_MAP: Record<string, BookStatus | undefined> = {
    completed: 'COMPLETED',
    pending: 'PENDING',
    translating: 'TRANSLATING',
    failed: 'FAILED',
};

function parsePage(value: string | null): number {
    const n = Number(value);
    return Number.isInteger(n) && n > 0 ? n : 1;
}

export async function loader({ request }: Route.LoaderArgs) {
    const url = new URL(request.url);
    const tab = url.searchParams.get('tab') ?? 'all';
    const page = parsePage(url.searchParams.get('page'));
    const fav = url.searchParams.get('fav') === '1';
    const q = (url.searchParams.get('q') ?? '').trim();
    const status = TAB_STATUS_MAP[tab];

    const body: Record<string, unknown> = { page, size: 10 };
    if (status) body.status = status;
    if (fav) body.is_favorite = true;
    if (q) body.q = q;

    try {
        const data = await serverFetch<PageResult<BookListItem>>(
            request,
            API_ENDPOINTS.TRANSLATE_LIST,
            { method: 'POST', body: JSON.stringify(body) },
        );
        return { items: data.items, total: data.total, page: data.page, size: data.size, currentTab: tab, fav, q, error: null };
    } catch (err) {
        if (err instanceof Response) throw err;
        return { items: [], total: 0, page: 1, size: 10, currentTab: tab, fav, q, error: '번역 이력을 불러오지 못했습니다.' };
    }
}

export function meta(_: Route.MetaArgs) {
    return [{ title: '번역 이력 | 해독 AI' }];
}

export default function HistoryRoute() {
    return <HistoryView />;
}
