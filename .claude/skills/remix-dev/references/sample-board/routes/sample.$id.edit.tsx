/**
 * [Golden File] 수정 Route 예시
 * 실제 위치: routes/sample.$id.edit.tsx  →  /board/sample/:id/edit
 *
 * 패턴 포인트:
 * - loader: 기존 데이터 조회 → defaultValues로 View에 주입
 * - action: 수정 처리 후 상세로 redirect
 * - default export: View 위임 (defaultValues + isEdit 전달)
 */

import { data, redirect, useLoaderData } from 'react-router';

import { SampleFormView } from '~/views/sample/SampleFormView';
import { getSampleDetail, updateSample } from '~/features/sample/api';
import { ApiError } from '~/shared/api/client';

import type { Route } from './+types/sample.$id.edit';

// ── loader ────────────────────────────────────────────
export async function loader({ params }: Route.LoaderArgs) {
    const { id } = params;

    try {
        const detail = await getSampleDetail(id!);
        return { detail };
    } catch (err) {
        if (err instanceof ApiError && err.code === 'UNAUTHORIZED') throw redirect('/login');
        throw data({ message: '데이터를 불러오지 못했습니다.' }, { status: 500 });
    }
}

// ── action ────────────────────────────────────────────
export async function action({ request, params }: Route.ActionArgs) {
    const formData = await request.formData();
    const intent = String(formData.get('intent'));

    if (intent === 'update') {
        try {
            await updateSample({
                id:       params.id!,
                title:    String(formData.get('title')),
                content:  String(formData.get('content')),
                category: String(formData.get('category')),
            });
            return redirect(`/board/sample/${params.id}`);
        } catch (err) {
            const message = err instanceof ApiError ? err.message : '수정에 실패했습니다.';
            return data({ success: false, error: message }, { status: 500 });
        }
    }

    return data({ success: false, error: 'Unknown intent' }, { status: 400 });
}

// ── Route (View 위임, defaultValues 주입) ─────────────
export default function SampleEditRoute() {
    const { detail } = useLoaderData<typeof loader>();

    return (
        <SampleFormView
            defaultValues={{
                title:    detail.title,
                content:  detail.content,
                category: detail.category,
            }}
            isEdit
        />
    );
}
