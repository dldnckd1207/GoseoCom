import { redirect } from 'react-router';

import { CommunityDetailView } from '~/views/community/CommunityDetailView';

import { ApiError } from '~/shared/api/client';
import { API_ENDPOINTS } from '~/shared/api/endpoints';
import { serverFetch } from '~/shared/api/server';

import type { Route } from './+types/_layout.community.$id';
import type { User } from '~/shared/types/auth';
import type { CommentItem, PageResult, PostDetail } from '~/shared/types/post';

export async function loader({ params, request }: Route.LoaderArgs) {
    const { id } = params;
    if (!id) throw redirect('/community');

    let user: User | null = null;
    try { user = await serverFetch<User>(request, API_ENDPOINTS.ME, undefined, { auth: 'optional' }); } catch { /* 비로그인 허용 */ }

    let post: PostDetail | null = null;
    let comments: CommentItem[] = [];
    let accessDenied = false;

    try {
        const [postData, commentsData] = await Promise.all([
            serverFetch<PostDetail>(request, API_ENDPOINTS.POST(id), undefined, { auth: 'optional' }),
            serverFetch<PageResult<CommentItem>>(
                request,
                API_ENDPOINTS.POST_COMMENTS_LIST(id),
                { method: 'POST', body: JSON.stringify({ page: 1, size: 50 }) },
                { auth: 'optional' },
            ),
        ]);
        post = postData;
        comments = commentsData.items;
    } catch (err) {
        if (err instanceof ApiError && err.status === 403) {
            accessDenied = true;
        } else {
            throw err;
        }
    }

    return { post, postId: id, comments, user, accessDenied };
}

export function meta({ data }: Route.MetaArgs) {
    return [{ title: `${data?.post?.title ?? '게시글'} | 해독 AI` }];
}

export async function action({ params, request }: Route.ActionArgs) {
    const { id } = params;
    const formData = await request.formData();
    const _action = String(formData.get('_action') ?? '');

    if (_action === 'delete') {
        let user: User | null = null;
        try { user = await serverFetch<User>(request, API_ENDPOINTS.ME, undefined, { auth: 'optional' }); } catch { /* 비로그인 */ }
        if (!user) return { ok: false, error: '로그인이 필요합니다.' };

        let post: PostDetail | null = null;
        try { post = await serverFetch<PostDetail>(request, API_ENDPOINTS.POST(id!), undefined, { auth: 'optional' }); } catch { /* 조회 실패 */ }
        if (!post) return { ok: false, error: '게시글을 찾을 수 없습니다.' };
        if (post.user_id !== user.user_id) return { ok: false, error: '삭제 권한이 없습니다.' };

        try {
            await serverFetch(request, API_ENDPOINTS.POST(id!), { method: 'DELETE' }, { auth: 'action' });
            return redirect('/community');
        } catch (err) {
            if (err instanceof ApiError) return { ok: false, error: err.message };
            return { ok: false, error: '게시글 삭제에 실패했습니다.' };
        }
    }

    const content = String(formData.get('content') ?? '').trim();
    if (!content) return { ok: false, error: '댓글 내용을 입력해주세요.' };

    try {
        await serverFetch(request, API_ENDPOINTS.POST_COMMENTS(id!), {
            method: 'POST',
            body: JSON.stringify({ content }),
        }, { auth: 'action' });
        return { ok: true };
    } catch (err) {
        if (err instanceof ApiError) return { ok: false, error: err.message };
        return { ok: false, error: '댓글 작성에 실패했습니다.' };
    }
}

export default function CommunityDetailRoute() {
    return <CommunityDetailView />;
}
