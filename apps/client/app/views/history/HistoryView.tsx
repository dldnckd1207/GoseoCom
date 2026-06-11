import { useEffect, useState } from 'react';

import { Link, useLoaderData, useRevalidator, useSearchParams } from 'react-router';

import { BookOpen, ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight, Plus, Star } from 'lucide-react';

import { apiClient } from '~/shared/api/client';
import { API_ENDPOINTS } from '~/shared/api/endpoints';
import { formatDate } from '~/shared/lib/date';
import { STATUS_BADGE } from '~/shared/lib/translateStatus';

import type { loader } from '~/routes/_protected.history._index';

const TABS = [
    { key: 'all',         label: '전체' },
    { key: 'completed',   label: '완료' },
    { key: 'pending',     label: '대기중' },
    { key: 'translating', label: '번역중' },
    { key: 'failed',      label: '실패' },
] as const;

const VALID_TABS = new Set(TABS.map((t) => t.key));

export function HistoryView() {
    const { items, total, page, size, currentTab, fav, q, error } = useLoaderData<typeof loader>();
    const [searchParams, setSearchParams] = useSearchParams();
    const revalidator = useRevalidator();

    const totalPages = Math.ceil(total / size) || 1;

    // 즐겨찾기 낙관적 업데이트
    const [pendingFavId, setPendingFavId] = useState<string | null>(null);
    const [optimisticFav, setOptimisticFav] = useState<Record<string, boolean>>({});

    // 검색창 입력 상태
    const [searchInput, setSearchInput] = useState(q);

    // URL의 q가 바뀌면 (뒤로가기/앞으로가기) 입력창 동기화
    useEffect(() => {
        setSearchInput(q);
    }, [q]);

    // 검색 debounce — URL 반영
    useEffect(() => {
        const timer = setTimeout(() => {
            const trimmed = searchInput.trim();
            setSearchParams(prev => {
                const next = new URLSearchParams(prev);
                if (trimmed === (next.get('q') ?? '')) return prev;
                if (trimmed) next.set('q', trimmed);
                else next.delete('q');
                next.delete('page');
                return next;
            }, { replace: true });
        }, 300);
        return () => clearTimeout(timer);
    }, [searchInput, setSearchParams]);

    // URL 파라미터 정규화
    useEffect(() => {
        const rawTab = searchParams.get('tab');
        const isInvalidTab = rawTab !== null && !VALID_TABS.has(rawTab as typeof TABS[number]['key']);
        const isPageOver = total > 0 && page > totalPages;

        if (!isInvalidTab && !isPageOver) return;

        const params = new URLSearchParams(searchParams);
        if (isInvalidTab) params.delete('tab');
        if (isPageOver) params.set('page', String(totalPages));
        setSearchParams(params, { replace: true });
    }, [searchParams, page, totalPages, total, setSearchParams]);

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

    const handleFavFilter = () => {
        const params = new URLSearchParams(searchParams);
        if (fav) params.delete('fav');
        else params.set('fav', '1');
        params.delete('page');
        setSearchParams(params);
    };

    const handleFavorite = async (e: React.MouseEvent, bookId: string, currentFav: boolean) => {
        e.preventDefault();
        if (pendingFavId) return;
        setPendingFavId(bookId);
        setOptimisticFav(prev => ({ ...prev, [bookId]: !currentFav }));
        try {
            await apiClient.put(API_ENDPOINTS.TRANSLATE_FAVORITE(bookId), {});
            await revalidator.revalidate();
            setOptimisticFav(prev => { const next = { ...prev }; delete next[bookId]; return next; });
        } catch {
            setOptimisticFav(prev => ({ ...prev, [bookId]: currentFav }));
        } finally {
            setPendingFavId(null);
        }
    };

    return (
        <div className="page-wrapper py-8">
            <div className="container-main">
                {/* 헤더 */}
                <div className="flex items-center justify-between mb-6">
                    <div>
                        <h1 className="text-[length:var(--text-page-title-mobile)] lg:text-[length:var(--text-page-title)] font-bold text-gray-900 mb-2">
                            번역 이력
                        </h1>
                        <p className="text-gray-600">내 고서 번역 이력을 확인하세요</p>
                    </div>
                    <Link
                        to="/translate"
                        className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
                    >
                        <Plus className="w-4 h-4" aria-hidden />
                        <span>새 번역</span>
                    </Link>
                </div>

                {/* 검색 + 즐겨찾기 필터 */}
                <div className="flex items-center gap-3 mb-4">
                    <div className="relative flex-1">
                        <input
                            type="text"
                            value={searchInput}
                            onChange={(e) => setSearchInput(e.target.value)}
                            placeholder="제목 검색..."
                            className="w-full rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm text-gray-800 placeholder:text-gray-400 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                        />
                    </div>
                    <button
                        type="button"
                        onClick={handleFavFilter}
                        className={`flex items-center gap-1.5 rounded-lg border px-3 py-2 text-sm font-medium transition-colors whitespace-nowrap ${
                            fav
                                ? 'border-yellow-400 bg-yellow-50 text-yellow-700'
                                : 'border-gray-300 bg-white text-gray-600 hover:border-gray-400'
                        }`}
                    >
                        <Star className={`w-4 h-4 ${fav ? 'fill-yellow-400 text-yellow-400' : ''}`} aria-hidden />
                        즐겨찾기
                    </button>
                </div>

                {/* 탭 */}
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
                    <div role="tablist" className="flex flex-wrap gap-2">
                        {TABS.map(({ key, label }) => (
                            <button
                                key={key}
                                type="button"
                                role="tab"
                                aria-selected={currentTab === key}
                                onClick={() => handleTabChange(key)}
                                className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
                                    currentTab === key
                                        ? 'bg-blue-600 text-white'
                                        : 'text-gray-600 hover:bg-gray-100'
                                }`}
                            >
                                {label}
                            </button>
                        ))}
                    </div>
                </div>

                {/* 오류 */}
                {error && (
                    <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 mb-6 text-sm text-red-700">
                        {error}
                    </div>
                )}

                {/* 목록 */}
                {items.length === 0 ? (
                    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 flex flex-col items-center justify-center text-center">
                        <BookOpen className="w-12 h-12 text-gray-300 mb-4" aria-hidden />
                        <p className="text-gray-500 font-medium mb-1">
                            {q || fav ? '검색 결과가 없습니다' : '번역 이력이 없습니다'}
                        </p>
                        <p className="text-sm text-gray-400">
                            {q || fav ? '다른 검색어나 필터를 시도해보세요' : '새 번역 버튼을 눌러 고서 번역을 시작해보세요'}
                        </p>
                    </div>
                ) : (
                    <div className="bg-white rounded-lg shadow-sm border border-gray-200 divide-y divide-gray-100">
                        {items.map((item) => {
                            const badge = STATUS_BADGE[item.status];
                            const isFav = optimisticFav[item.book_id] ?? item.is_favorite;
                            const isPending = pendingFavId === item.book_id;
                            return (
                                <div
                                    key={item.book_id}
                                    className="flex items-center justify-between px-4 py-4 hover:bg-gray-50 transition-colors"
                                >
                                    <Link
                                        to={`/history/${item.book_id}`}
                                        className="flex items-center gap-3 min-w-0 flex-1"
                                    >
                                        <BookOpen className="w-5 h-5 text-gray-400 shrink-0" aria-hidden />
                                        <span className="text-gray-900 font-medium truncate">{item.title}</span>
                                    </Link>
                                    <div className="flex items-center gap-3 ml-4 shrink-0">
                                        <span className={`text-xs font-medium px-2 py-1 rounded-full border ${badge.className}`}>
                                            {badge.label}
                                        </span>
                                        <span className="text-sm text-gray-400 hidden sm:block">
                                            {formatDate(item.created_at)}
                                        </span>
                                        <button
                                            type="button"
                                            onClick={(e) => handleFavorite(e, item.book_id, item.is_favorite)}
                                            disabled={isPending}
                                            aria-pressed={isFav}
                                            aria-label={isFav ? '즐겨찾기 해제' : '즐겨찾기 추가'}
                                            className="p-1.5 rounded-md transition-colors hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
                                        >
                                            <Star
                                                className={`w-4 h-4 transition-colors ${
                                                    isFav ? 'fill-yellow-400 text-yellow-400' : 'text-gray-300 hover:text-yellow-400'
                                                }`}
                                                aria-hidden
                                            />
                                        </button>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                )}

                {/* 페이지네이션 */}
                {totalPages > 1 && (
                    <div className="flex justify-center items-center gap-1 mt-6">
                        <button
                            type="button"
                            onClick={() => handlePageChange(1)}
                            disabled={page === 1}
                            className="p-2 rounded-md text-gray-500 hover:bg-gray-100 disabled:opacity-30 disabled:cursor-not-allowed"
                            aria-label="첫 페이지"
                        >
                            <ChevronsLeft className="w-4 h-4" aria-hidden />
                        </button>
                        <button
                            type="button"
                            onClick={() => handlePageChange(page - 1)}
                            disabled={page === 1}
                            className="p-2 rounded-md text-gray-500 hover:bg-gray-100 disabled:opacity-30 disabled:cursor-not-allowed"
                            aria-label="이전 페이지"
                        >
                            <ChevronLeft className="w-4 h-4" aria-hidden />
                        </button>
                        {Array.from({ length: totalPages }, (_, i) => i + 1)
                            .filter((p) => Math.abs(p - page) <= 2)
                            .map((p) => (
                                <button
                                    key={p}
                                    type="button"
                                    onClick={() => handlePageChange(p)}
                                    aria-current={p === page ? 'page' : undefined}
                                    className={`w-9 h-9 rounded-md text-sm font-medium transition-colors ${
                                        p === page
                                            ? 'bg-blue-600 text-white'
                                            : 'text-gray-600 hover:bg-gray-100'
                                    }`}
                                >
                                    {p}
                                </button>
                            ))}
                        <button
                            type="button"
                            onClick={() => handlePageChange(page + 1)}
                            disabled={page === totalPages}
                            className="p-2 rounded-md text-gray-500 hover:bg-gray-100 disabled:opacity-30 disabled:cursor-not-allowed"
                            aria-label="다음 페이지"
                        >
                            <ChevronRight className="w-4 h-4" aria-hidden />
                        </button>
                        <button
                            type="button"
                            onClick={() => handlePageChange(totalPages)}
                            disabled={page === totalPages}
                            className="p-2 rounded-md text-gray-500 hover:bg-gray-100 disabled:opacity-30 disabled:cursor-not-allowed"
                            aria-label="마지막 페이지"
                        >
                            <ChevronsRight className="w-4 h-4" aria-hidden />
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
}
