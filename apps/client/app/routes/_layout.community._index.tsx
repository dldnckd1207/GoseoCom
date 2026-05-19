import { CommunityListView } from '~/views/community/CommunityListView';

import { API_ENDPOINTS } from '~/shared/api/endpoints';
import { serverFetch } from '~/shared/api/server';

import type { Route } from './+types/_layout.community._index';
import type { User } from '~/shared/types/auth';
import type { BoardSummary, PageResult, PostSummary } from '~/shared/types/post';

function parsePage(value: string | null): number {
    const n = Number(value);
    return Number.isInteger(n) && n > 0 ? n : 1;
}

export async function loader({ request }: Route.LoaderArgs) {
    const url = new URL(request.url);
    const tab  = url.searchParams.get('tab') ?? 'all';
    const page = parsePage(url.searchParams.get('page'));

    let user: User | null = null;
    try { user = await serverFetch<User>(request, API_ENDPOINTS.ME, undefined, { auth: 'optional' }); } catch { /* 비로그인 허용 */ }

    let boards: BoardSummary[] = [];
    let boardsError: string | null = null;

    try {
        const boardsData = await serverFetch<PageResult<BoardSummary>>(
            request,
            API_ENDPOINTS.BOARDS_LIST,
            { method: 'POST', body: JSON.stringify({ board_group: 'community', page: 1, size: 100 }) },
            { auth: 'optional' },
        );
        boards = boardsData.items;
    } catch {
        boardsError = '게시판 정보를 불러오지 못했습니다. 잠시 후 다시 시도해주세요.';
    }

    // 유효하지 않은 tab이면 'all'로 fallback (빈 배열 → BE 422 방지)
    const matchedBoards = boards.filter(b => b.board_code === tab);
    const effectiveTab = tab === 'all' || matchedBoards.length === 0 ? 'all' : tab;
    const boardCodes = effectiveTab === 'all'
        ? boards.map(b => b.board_code)
        : matchedBoards.map(b => b.board_code);

    if (boardCodes.length === 0) {
        return { boards, posts: [], total: 0, page: 1, size: 20, currentTab: effectiveTab, user, error: boardsError };
    }

    let posts: PostSummary[] = [];
    let total = 0;
    let responsePage = page;
    let responseSize = 20;
    let postsError: string | null = null;

    try {
        const data = await serverFetch<PageResult<PostSummary>>(
            request,
            API_ENDPOINTS.POSTS_LIST,
            { method: 'POST', body: JSON.stringify({ board_codes: boardCodes, page, size: 20 }) },
            { auth: 'optional' },
        );
        posts = data.items;
        total = data.total;
        responsePage = data.page;
        responseSize = data.size;
    } catch {
        postsError = '게시글 목록을 불러오지 못했습니다. 잠시 후 다시 시도해주세요.';
    }

    return {
        boards,
        posts,
        total,
        page: responsePage,
        size: responseSize,
        currentTab: effectiveTab,
        user,
        error: boardsError ?? postsError,
    };
}

export function meta(_: Route.MetaArgs) {
    return [
        { title: '커뮤니티 | 해독 AI' },
        { name: 'description', content: '고서 해독에 대한 의견을 나누고 질문해보세요.' },
    ];
}

export default function CommunityRoute() {
    return <CommunityListView />;
}
