import { TranslateView } from '~/views/translate/TranslateView';

import { ApiError } from '~/shared/api/client';
import { API_ENDPOINTS } from '~/shared/api/endpoints';
import { parseCsrfToken, serverFetch } from '~/shared/api/server';

import type { Route } from './+types/_protected.translate';
import type { ApiWrappedResponse } from '~/shared/api/client';
import type { BookResult, FileUploadResult } from '~/shared/types/translate';

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

export async function loader({ request }: Route.LoaderArgs) {
    const url = new URL(request.url);
    const bookId = url.searchParams.get('book_id');
    if (!bookId) return { initialBook: null };

    try {
        const book = await serverFetch<BookResult>(
            request,
            API_ENDPOINTS.TRANSLATE_DETAIL(bookId),
            { method: 'GET' },
            { auth: 'required' },
        );
        if (book.status === 'OCR_COMPLETED') return { initialBook: book };
    } catch {
        // 조회 실패 시 그냥 idle 상태로 시작
    }
    return { initialBook: null };
}

export async function action({ request }: Route.ActionArgs) {
    const formData = await request.formData();
    const file = formData.get('file') as File | null;

    if (!file || file.size === 0) {
        return { ok: false as const, error: '파일을 선택해주세요.' };
    }

    // 1단계: 이미지 업로드 (multipart — serverFetch Content-Type 고정 우회)
    const cookie = request.headers.get('cookie') ?? '';
    const uploadForm = new FormData();
    uploadForm.append('file', file);

    // double-submit CSRF: raw fetch라 serverFetch가 안 붙여주는 X-CSRF-Token을 직접 추가 (보안 #7)
    const uploadHeaders: Record<string, string> = { cookie };
    const csrf = parseCsrfToken(cookie);
    if (csrf) uploadHeaders['X-CSRF-Token'] = csrf;

    let fileId: string;
    try {
        const uploadRes = await fetch(`${BASE_URL}${API_ENDPOINTS.UPLOADS}`, {
            method: 'POST',
            headers: uploadHeaders,
            body: uploadForm,
        });
        const uploadJson: ApiWrappedResponse<FileUploadResult> = await uploadRes.json();
        if (!uploadJson.header.success) {
            return { ok: false as const, error: uploadJson.header.message ?? '업로드에 실패했습니다.' };
        }
        const fileData = uploadJson.body.data;
        if (!fileData?.file_id) {
            return { ok: false as const, error: '업로드에 실패했습니다.' };
        }
        fileId = fileData.file_id;
    } catch {
        return { ok: false as const, error: '업로드 중 오류가 발생했습니다.' };
    }

    // 2단계: OCR 시작
    try {
        const result = await serverFetch<{ book_id: string; status: string }>(
            request,
            API_ENDPOINTS.TRANSLATE_OCR,
            { method: 'POST', body: JSON.stringify({ file_id: fileId }) },
            { auth: 'action' },
        );
        return { ok: true as const, bookId: result.book_id };
    } catch (err) {
        if (err instanceof Response) throw err;
        if (err instanceof ApiError) return { ok: false as const, error: err.message, errorCode: err.code };
        return { ok: false as const, error: 'OCR 시작에 실패했습니다.', errorCode: null };
    }
}

export function meta(_: Route.MetaArgs) {
    return [{ title: '번역하기 | 해독 AI' }];
}

export default function TranslateRoute() {
    return <TranslateView />;
}
