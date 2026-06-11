import { isRouteErrorResponse, useRouteError } from 'react-router';

import { TranslateTestView } from '~/views/translate-test/TranslateTestView';

import { ApiError } from '~/shared/api/client';
import { API_ENDPOINTS } from '~/shared/api/endpoints';
import { serverFetch } from '~/shared/api/server';

import type { Route } from './+types/_protected.translate-test';
import type { BookDropdownItem, LearnWorkspaceResponse } from '~/features/learn';

type LoaderData =
    | { mode: 'select'; books: BookDropdownItem[]; error: string | null }
    | { mode: 'workspace'; workspace: LearnWorkspaceResponse };

async function loadBookList(request: Request, error: string | null = null): Promise<LoaderData> {
    const books = await serverFetch<BookDropdownItem[]>(
        request,
        API_ENDPOINTS.TRANSLATE_MINE,
        { method: 'GET' },
        { auth: 'required' },
    );
    return { mode: 'select', books, error };
}

export async function loader({ request }: Route.LoaderArgs): Promise<LoaderData> {
    const url = new URL(request.url);
    const bookId = url.searchParams.get('book_id');

    if (!bookId) return loadBookList(request);

    try {
        const workspace = await serverFetch<LearnWorkspaceResponse>(
            request,
            API_ENDPOINTS.LEARN_WORKSPACE(bookId),
            { method: 'GET' },
            { auth: 'required' },
        );
        return { mode: 'workspace', workspace };
    } catch (err) {
        // 접근 불가(400/403/404) 시 선택 화면으로 폴백 — redirect/Response는 그대로 전파
        if (err instanceof ApiError) return loadBookList(request, err.message);
        throw err;
    }
}

export function meta(_: Route.MetaArgs) {
    return [{ title: '학습하기 (Beta) | 해독 AI' }];
}

export function ErrorBoundary() {
    const error = useRouteError();
    const message = isRouteErrorResponse(error)
        ? (error.data?.message ?? '요청을 처리하지 못했습니다.')
        : '예상치 못한 오류가 발생했습니다.';

    return (
        <div className="page-wrapper py-8">
            <div className="container-main">
                <div className="rounded-2xl border border-gray-200 bg-white p-10 text-center shadow-sm">
                    <p className="font-medium text-gray-700">{message}</p>
                    <p className="mt-1 text-sm text-gray-500">잠시 후 다시 시도해 주세요.</p>
                </div>
            </div>
        </div>
    );
}

export default function TranslateTestRoute() {
    return <TranslateTestView />;
}
