import { useEffect, useMemo } from 'react';

import { Link, useNavigate, useSearchParams, useLoaderData } from 'react-router';

import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight, Pencil } from 'lucide-react';

import { formatDate } from '~/shared/lib/date';
import { openModal } from '~/shared/ui/modal';

import type { loader } from '~/routes/_layout.community._index';

export function CommunityListView() {
    const { boards, posts, total, page, size, currentTab, user, error } = useLoaderData<typeof loader>();
    const navigate = useNavigate();
    const [searchParams, setSearchParams] = useSearchParams();

    const totalPages = Math.ceil(total / size) || 1;
    const validCodes = useMemo(() => boards.map(b => b.board_code), [boards]);
    const boardMap = useMemo(() => new Map(boards.map(b => [b.board_code, b] as const)), [boards]);

    // invalid tab 또는 page 초과 → URL 정규화
    useEffect(() => {
        const rawTab = searchParams.get('tab');
        const isInvalidTab = rawTab !== null && rawTab !== 'all' && !validCodes.includes(rawTab);
        const isPageOver = total > 0 && page > totalPages;

        if (!isInvalidTab && !isPageOver) return;

        const params = new URLSearchParams(searchParams);
        if (isInvalidTab) params.delete('tab');
        if (isPageOver) params.set('page', String(totalPages));
        setSearchParams(params, { replace: true });
    }, [searchParams, validCodes, page, totalPages, total, setSearchParams]);

    const handleTabChange = (tab: string) => {
        const params = new URLSearchParams(searchParams);
        if (tab === 'all') params.delete('tab');
        else params.set('tab', tab);
        params.delete('page');
        setSearchParams(params);
    };

    const handlePageChange = (newPage: number) => {
        const params = new URLSearchParams(searchParams);
        if (newPage === 1) params.delete('page');
        else params.set('page', String(newPage));
        setSearchParams(params);
    };

    const handleWriteClick = () => {
        const writePath = currentTab === 'all'
            ? '/community/write'
            : `/community/write?board=${encodeURIComponent(currentTab)}`;
        if (!user) {
            openModal({
                type: 'alert',
                message: '로그인이 필요한 서비스입니다.',
                buttons: [{ label: '확인', onClick: () => navigate(`/login?redirect=${encodeURIComponent(writePath)}`) }],
            });
            return;
        }
        navigate(writePath);
    };

    return (
        <div className="page-wrapper py-8">
            <div className="container-main">
                <div className="mb-8">
                    <h1 className="text-[length:var(--text-page-title-mobile)] lg:text-[length:var(--text-page-title)] font-bold text-gray-900 mb-2">커뮤니티</h1>
                    <p className="text-gray-600">고서 해독에 대한 의견을 나누고 질문해보세요</p>
                </div>

                {/* 탭 메뉴 */}
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
                    <div role="tablist" className="flex flex-wrap gap-2">
                        <button
                            key="all"
                            type="button"
                            role="tab"
                            aria-selected={currentTab === 'all'}
                            onClick={() => handleTabChange('all')}
                            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                                currentTab === 'all'
                                    ? 'bg-blue-600 text-white shadow-sm'
                                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                            }`}
                        >
                            전체
                        </button>
                        {boards.map(board => (
                            <button
                                key={board.board_code}
                                type="button"
                                role="tab"
                                aria-selected={currentTab === board.board_code}
                                onClick={() => handleTabChange(board.board_code)}
                                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                                    currentTab === board.board_code
                                        ? 'bg-blue-600 text-white shadow-sm'
                                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                                }`}
                            >
                                {board.board_name}
                            </button>
                        ))}
                    </div>
                </div>

                {/* 작성 버튼 */}
                <div className="flex justify-end mb-6">
                    <button
                        type="button"
                        onClick={handleWriteClick}
                        className="bg-blue-600 text-white px-6 py-2 rounded-lg font-medium hover:bg-blue-700 transition-colors shadow-sm flex items-center gap-2"
                    >
                        <Pencil className="w-5 h-5" aria-hidden />
                        <span>글 작성하기</span>
                    </button>
                </div>

                {/* API 에러 메시지 */}
                {error && (
                    <div className="bg-red-50 border border-red-200 rounded-lg px-6 py-4 mb-6 text-red-700 text-sm">
                        {error}
                    </div>
                )}

                {/* 게시글 목록 */}
                {posts.length === 0 ? (
                    <div className="bg-white rounded-lg border border-gray-200 px-6 py-12 text-center text-gray-500">
                        게시글이 없습니다.
                    </div>
                ) : (
                    <>
                        {/* 모바일: 카드 그리드 */}
                        <div className="md:hidden grid grid-cols-1 gap-3">
                            {posts.map(post => {
                                const board = boardMap.get(post.board_code);
                                return (
                                    <Link
                                        key={post.id}
                                        to={`/community/${post.id}`}
                                        className="block rounded-lg border border-gray-200 bg-white p-4 hover:shadow-md transition-shadow"
                                    >
                                        <div className="flex flex-wrap items-center gap-1 mb-2">
                                            <span className="inline-block max-w-full truncate bg-gray-100 text-gray-600 text-xs px-2 py-0.5 rounded-full">
                                                {board?.board_name ?? post.board_code}
                                            </span>
                                            {post.category_name && (
                                                <span className="inline-block max-w-full truncate bg-blue-50 text-blue-600 text-xs px-2 py-0.5 rounded-full">
                                                    {post.category_name}
                                                </span>
                                            )}
                                        </div>
                                        <h3 className="text-gray-900 font-medium line-clamp-2 mb-2">
                                            {post.title}
                                        </h3>
                                        <div className="flex items-center gap-2 text-xs text-gray-400">
                                            <span className="min-w-0 truncate">{post.author_name}</span>
                                            <span className="shrink-0">{formatDate(post.created_at)}</span>
                                        </div>
                                        <div className="flex items-center gap-3 mt-1 text-xs text-gray-400">
                                            <span>조회 {post.view_count}</span>
                                            <span>댓글 {post.comment_count}</span>
                                        </div>
                                    </Link>
                                );
                            })}
                        </div>

                        {/* 데스크탑: 테이블 목록 */}
                        <div className="hidden md:block bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
                            <div className="grid grid-cols-12 bg-gray-50 border-b border-gray-200 px-6 py-3 text-sm font-semibold text-gray-700">
                                <div className="col-span-5">제목</div>
                                <div className="col-span-2">게시판</div>
                                <div className="col-span-2">작성자</div>
                                <div className="col-span-1 text-center">조회</div>
                                <div className="col-span-1 text-center">댓글</div>
                                <div className="col-span-1">작성일</div>
                            </div>
                            <div className="divide-y divide-gray-200">
                                {posts.map(post => {
                                    const board = boardMap.get(post.board_code);
                                    return (
                                        <Link
                                            key={post.id}
                                            to={`/community/${post.id}`}
                                            className="block px-6 py-4 hover:bg-gray-50 transition-colors"
                                        >
                                            <div className="grid grid-cols-12 gap-4 items-center">
                                                <div className="col-span-5">
                                                    <h3 className="text-gray-900 font-medium hover:text-blue-600 transition-colors line-clamp-1">
                                                        {post.title}
                                                    </h3>
                                                </div>
                                                <div className="col-span-2 flex flex-wrap items-center gap-1">
                                                    <span className="inline-block bg-gray-100 text-gray-700 text-sm px-3 py-1 rounded-full">
                                                        {board?.board_name ?? post.board_code}
                                                    </span>
                                                    {post.category_name && (
                                                        <span className="inline-block bg-blue-50 text-blue-600 text-xs px-2 py-1 rounded-full">
                                                            {post.category_name}
                                                        </span>
                                                    )}
                                                </div>
                                                <div className="col-span-2 text-sm text-gray-600">{post.author_name}</div>
                                                <div className="col-span-1 text-sm text-gray-500 text-center">{post.view_count}</div>
                                                <div className="col-span-1 text-sm text-gray-500 text-center">{post.comment_count}</div>
                                                <div className="col-span-1 text-sm text-gray-500">{formatDate(post.created_at)}</div>
                                            </div>
                                        </Link>
                                    );
                                })}
                            </div>
                        </div>
                    </>
                )}

                {/* 페이지네이션 */}
                <div className="mt-6 flex justify-center">
                    <div className="flex gap-2">
                        <button
                            type="button"
                            onClick={() => handlePageChange(1)}
                            disabled={page === 1}
                            className="px-3 py-2 rounded-lg font-medium bg-white text-gray-700 border border-gray-300 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed"
                            aria-label="첫 페이지"
                        >
                            <ChevronsLeft className="w-4 h-4" aria-hidden />
                        </button>
                        <button
                            type="button"
                            onClick={() => handlePageChange(page - 1)}
                            disabled={page === 1}
                            className="px-3 py-2 rounded-lg font-medium bg-white text-gray-700 border border-gray-300 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed"
                            aria-label="이전 페이지"
                        >
                            <ChevronLeft className="w-4 h-4" aria-hidden />
                        </button>
                        {Array.from({ length: totalPages }, (_, i) => i + 1)
                            .filter(p => Math.abs(p - page) <= 2)
                            .map(p => (
                                <button
                                    key={p}
                                    type="button"
                                    onClick={() => handlePageChange(p)}
                                    className={`px-4 py-2 rounded-lg font-medium ${
                                        p === page
                                            ? 'bg-blue-600 text-white'
                                            : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                                    }`}
                                >
                                    {p}
                                </button>
                            ))}
                        <button
                            type="button"
                            onClick={() => handlePageChange(page + 1)}
                            disabled={page === totalPages}
                            className="px-3 py-2 rounded-lg font-medium bg-white text-gray-700 border border-gray-300 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed"
                            aria-label="다음 페이지"
                        >
                            <ChevronRight className="w-4 h-4" aria-hidden />
                        </button>
                        <button
                            type="button"
                            onClick={() => handlePageChange(totalPages)}
                            disabled={page === totalPages}
                            className="px-3 py-2 rounded-lg font-medium bg-white text-gray-700 border border-gray-300 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed"
                            aria-label="마지막 페이지"
                        >
                            <ChevronsRight className="w-4 h-4" aria-hidden />
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
