/**
 * [Golden File] 목록 Route 예시
 * 실제 위치: routes/sample._index.tsx  →  /board/sample
 *
 * 패턴 포인트:
 * - loader: 서버에서 목록 데이터 조회
 * - action: 삭제 처리
 * - default export: View 위임만
 * - ErrorBoundary: route 단위 에러 처리
 */

import { data, redirect, useRouteError, isRouteErrorResponse } from 'react-router';

import { SampleView } from '~/views/sample/SampleView';
import { getSampleList, deleteSample } from '~/features/sample/api';
import { ApiError } from '~/shared/api/client';

import type { Route } from './+types/sample._index';

// ── loader ────────────────────────────────────────────
export async function loader({ request }: Route.LoaderArgs) {
    const url = new URL(request.url);
    const page = Number(url.searchParams.get('page') ?? '1');
    const keyword = url.searchParams.get('keyword') ?? '';
    const category = url.searchParams.get('category') ?? '';

    try {
        const result = await getSampleList({
            page,
            size: 10,
            keyword: keyword || undefined,
            category: category || undefined,
        });
        return { data: result };
    } catch (err) {
        if (err instanceof ApiError && err.code === 'UNAUTHORIZED') {
            throw redirect('/login');
        }
        throw data({ message: '목록을 불러오지 못했습니다.' }, { status: 500 });
    }
}

// ── action ────────────────────────────────────────────
export async function action({ request }: Route.ActionArgs) {
    const formData = await request.formData();
    const intent = String(formData.get('intent'));

    if (intent === 'delete') {
        const id = String(formData.get('id'));
        try {
            await deleteSample({ id });
            return { success: true };
        } catch (err) {
            const message = err instanceof ApiError ? err.message : '삭제에 실패했습니다.';
            return data({ success: false, error: message }, { status: 500 });
        }
    }

    return data({ success: false, error: 'Unknown intent' }, { status: 400 });
}

// ── Route (View 위임) ─────────────────────────────────
export default function SampleRoute() {
    return <SampleView />;
}

// ── ErrorBoundary ─────────────────────────────────────
export function ErrorBoundary() {
    const error = useRouteError();

    if (isRouteErrorResponse(error)) {
        return (
            <div className="state-error">
                <p>{error.data?.message ?? '오류가 발생했습니다.'}</p>
            </div>
        );
    }

    return <div className="state-error"><p>예상치 못한 오류가 발생했습니다.</p></div>;
}
