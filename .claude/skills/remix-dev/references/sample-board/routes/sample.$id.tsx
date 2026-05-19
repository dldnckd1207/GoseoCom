/**
 * [Golden File] 상세 Route 예시
 * 실제 위치: routes/sample.$id.tsx  →  /board/sample/:id
 *
 * 패턴 포인트:
 * - loader: params.id로 단건 조회
 * - action: 삭제 처리 (상세 페이지에서 삭제)
 * - default export: View 위임만
 */

import { data, redirect, useRouteError, isRouteErrorResponse } from 'react-router';

import { SampleDetailView } from '~/views/sample/SampleDetailView';
import { getSampleDetail, deleteSample } from '~/features/sample/api';
import { ApiError } from '~/shared/api/client';

import type { Route } from './+types/sample.$id';

// ── loader ────────────────────────────────────────────
export async function loader({ params }: Route.LoaderArgs) {
    const { id } = params;

    try {
        const detail = await getSampleDetail(id!);
        return { detail };
    } catch (err) {
        if (err instanceof ApiError) {
            if (err.code === 'UNAUTHORIZED') throw redirect('/login');
            if (err.code === 'NOT_FOUND') throw data({ message: '게시글을 찾을 수 없습니다.' }, { status: 404 });
        }
        throw data({ message: '상세 정보를 불러오지 못했습니다.' }, { status: 500 });
    }
}

// ── action ────────────────────────────────────────────
export async function action({ request, params }: Route.ActionArgs) {
    const formData = await request.formData();
    const intent = String(formData.get('intent'));

    if (intent === 'delete') {
        const id = String(formData.get('id') ?? params.id);
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
export default function SampleDetailRoute() {
    return <SampleDetailView />;
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
