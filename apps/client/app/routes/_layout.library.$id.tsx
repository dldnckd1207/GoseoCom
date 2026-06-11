import { LibraryDetailView } from '~/views/library/LibraryDetailView';

import { ApiError } from '~/shared/api/client';
import { API_ENDPOINTS } from '~/shared/api/endpoints';
import { serverFetch } from '~/shared/api/server';

import type { Route } from './+types/_layout.library.$id';
import type { BookResult } from '~/shared/types/translate';

export async function loader({ request, params }: Route.LoaderArgs) {
    try {
        const book = await serverFetch<BookResult>(
            request,
            API_ENDPOINTS.TRANSLATE_PUBLIC_DETAIL(params.id),
            undefined,
            { auth: 'optional' },
        );
        return { book };
    } catch (err) {
        if (err instanceof Response) throw err;
        if (err instanceof ApiError && err.status === 404) {
            throw new Response('Not Found', { status: 404 });
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
