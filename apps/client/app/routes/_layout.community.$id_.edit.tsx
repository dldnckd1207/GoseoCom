import { redirect } from 'react-router';

import { CommunityEditView } from '~/views/community/CommunityEditView';

import { ApiError } from '~/shared/api/client';
import { API_ENDPOINTS } from '~/shared/api/endpoints';
import { serverFetch } from '~/shared/api/server';

import type { Route } from './+types/_layout.community.$id_.edit';
import type { User } from '~/shared/types/auth';
import type { BoardCategoryItem, PostDetail } from '~/shared/types/post';
import type { BookDropdownItem } from '~/shared/types/translate';

export async function loader({ params, request }: Route.LoaderArgs) {
    const { id } = params;
    if (!id) throw redirect('/community');

    let user: User | null = null;
    try { user = await serverFetch<User>(request, API_ENDPOINTS.ME, undefined, { auth: 'required' }); }
    catch (err) { if (err instanceof Response) throw err; }
    if (!user) throw redirect(`/login?redirect=${encodeURIComponent(`/community/${id}/edit`)}`);

    let post: PostDetail;
    try {
        post = await serverFetch<PostDetail>(request, API_ENDPOINTS.POST(id), undefined, { auth: 'optional' });
    } catch {
        throw redirect('/community');
    }
    if (post.user_id !== user.user_id) throw redirect(`/community/${id}`);

    let myBooks: BookDropdownItem[] = [];
    try {
        myBooks = await serverFetch<BookDropdownItem[]>(
            request, API_ENDPOINTS.TRANSLATE_MINE, undefined, { auth: 'required' }
        );
    } catch (err) {
        if (err instanceof Response) throw err;
    }

    let categories: BoardCategoryItem[] = [];
    try {
        categories = await serverFetch<BoardCategoryItem[]>(
            request,
            API_ENDPOINTS.BOARD_CATEGORIES(post.board_code),
            undefined,
            { auth: 'optional' },
        );
    } catch { /* 카테고리 없는 게시판은 빈 배열 */ }

    return { post, postId: id, myBooks, categories };
}

export async function action({ params, request }: Route.ActionArgs) {
    const { id } = params;
    let user: User | null = null;
    try { user = await serverFetch<User>(request, API_ENDPOINTS.ME, undefined, { auth: 'optional' }); } catch { /* 비로그인 */ }
    if (!user) throw redirect(`/login?redirect=${encodeURIComponent(`/community/${id}/edit`)}`);

    let post: PostDetail;
    try {
        post = await serverFetch<PostDetail>(request, API_ENDPOINTS.POST(id!), undefined, { auth: 'optional' });
    } catch { throw redirect('/community'); }
    if (post.user_id !== user.user_id) throw redirect(`/community/${id}`);

    const formData = await request.formData();
    const title       = String(formData.get('title') ?? '').trim();
    const content     = String(formData.get('content') ?? '').trim();
    const category_id = String(formData.get('category_id') ?? '').trim() || null;
    const book_id     = String(formData.get('book_id') ?? '').trim() || null;

    if (!title || !content) return { ok: false, error: '제목과 내용을 입력해주세요.' };

    try {
        await serverFetch(request, API_ENDPOINTS.POST(id!), {
            method: 'PUT',
            body: JSON.stringify({ title, content, category_id, book_id }),
        }, { auth: 'action' });
        return redirect(`/community/${id}`);
    } catch (err) {
        if (err instanceof ApiError) return { ok: false, error: err.message };
        return { ok: false, error: '게시글 수정에 실패했습니다.' };
    }
}

export function meta({ data }: Route.MetaArgs) {
    return [{ title: `${data?.post?.title ?? '게시글'} 수정 | 해독 AI` }];
}

export default function CommunityEditRoute() {
    return <CommunityEditView />;
}
