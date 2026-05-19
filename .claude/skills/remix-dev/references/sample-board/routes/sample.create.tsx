/**
 * [Golden File] 등록 Route 예시
 * 실제 위치: routes/sample.create.tsx  →  /board/sample/create
 *
 * 패턴 포인트:
 * - action: 생성 처리 후 목록으로 redirect
 * - default export: View 위임만 (defaultValues 불필요)
 */

import { data, redirect } from 'react-router';

import { SampleFormView } from '~/views/sample/SampleFormView';
import { createSample } from '~/features/sample/api';
import { ApiError } from '~/shared/api/client';

import type { Route } from './+types/sample.create';

// ── action ────────────────────────────────────────────
export async function action({ request }: Route.ActionArgs) {
    const formData = await request.formData();
    const intent = String(formData.get('intent'));

    if (intent === 'create') {
        try {
            await createSample({
                title:    String(formData.get('title')),
                content:  String(formData.get('content')),
                category: String(formData.get('category')),
            });
            return redirect('/board/sample');
        } catch (err) {
            const message = err instanceof ApiError ? err.message : '등록에 실패했습니다.';
            return data({ success: false, error: message }, { status: 500 });
        }
    }

    return data({ success: false, error: 'Unknown intent' }, { status: 400 });
}

// ── Route (View 위임) ─────────────────────────────────
export default function SampleCreateRoute() {
    return <SampleFormView />;
}
