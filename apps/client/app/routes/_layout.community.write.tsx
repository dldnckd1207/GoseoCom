import { redirect } from 'react-router';

import { CommunityWriteView } from '~/views/community/CommunityWriteView';

import { ApiError } from '~/shared/api/client';
import { API_ENDPOINTS } from '~/shared/api/endpoints';
import { serverFetch } from '~/shared/api/server';

import type { Route } from './+types/_layout.community.write';
import type { User } from '~/shared/types/auth';
import type { BoardCategoryItem, BoardSummary, PageResult, PostDetail } from '~/shared/types/post';

export async function loader({ request }: Route.LoaderArgs) {
    const url = new URL(request.url);

    let user: User | null = null;
    try { user = await serverFetch<User>(request, API_ENDPOINTS.ME, undefined, { auth: 'required' }); } catch (err) { if (err instanceof Response) throw err; }
    if (!user) throw redirect(`/login?redirect=${encodeURIComponent(url.pathname + url.search)}`);

    let writableBoards: BoardSummary[] = [];
    try {
        const boardsData = await serverFetch<PageResult<BoardSummary>>(
            request,
            API_ENDPOINTS.BOARDS_LIST,
            { method: 'POST', body: JSON.stringify({ board_group: 'community', page: 1, size: 100 }) },
            { auth: 'optional' },
        );
        writableBoards = boardsData.items.filter(b => b.write_yn);
    } catch { /* 게시판 API 실패 시 빈 목록으로 fallback */ }

    const boardParam = url.searchParams.get('board') ?? '';
    const matched = writableBoards.find(b => b.board_code === boardParam);
    const defaultBoard = matched?.board_code ?? writableBoards[0]?.board_code ?? '';

    // 각 게시판의 카테고리를 병렬 조회 — 일부 실패해도 해당 board만 빈 배열로 처리
    const categories: Record<string, BoardCategoryItem[]> = {};
    if (writableBoards.length > 0) {
        const results = await Promise.allSettled(
            writableBoards.map(async (b) => {
                const cats = await serverFetch<BoardCategoryItem[]>(
                    request,
                    API_ENDPOINTS.BOARD_CATEGORIES(b.board_code),
                    undefined,
                    { auth: 'optional' },
                );
                return { board_code: b.board_code, categories: cats };
            }),
        );
        for (const r of results) {
            if (r.status === 'fulfilled') categories[r.value.board_code] = r.value.categories;
        }
    }

    return { boards: writableBoards, user, defaultBoard, categories };
}

export async function action({ request }: Route.ActionArgs) {
    const formData = await request.formData();
    const board_code = String(formData.get('board_code') ?? '').trim();
    const title      = String(formData.get('title') ?? '').trim();
    const content    = String(formData.get('content') ?? '').trim();
    const category_id = String(formData.get('category_id') ?? '').trim() || null;

    if (!board_code || !title || !content) {
        return { ok: false, error: '필수 항목을 모두 입력해주세요.' };
    }

    try {
        const post = await serverFetch<PostDetail>(request, API_ENDPOINTS.POSTS, {
            method: 'POST',
            body: JSON.stringify({ board_code, title, content, category_id }),
        }, { auth: 'action' });
        return redirect(`/community/${post.id}`);
    } catch (err) {
        if (err instanceof ApiError) return { ok: false, error: err.message };
        return { ok: false, error: '게시글 작성에 실패했습니다.' };
    }
}

export function meta(_: Route.MetaArgs) {
    return [{ title: '글 작성 | 해독 AI' }];
}

export default function CommunityWriteRoute() {
    return <CommunityWriteView />;
}
