import { useEffect } from 'react';

import { Link, useLoaderData, useSearchParams } from 'react-router';

import { BookOpen, ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight, Plus } from 'lucide-react';

import { formatDate } from '~/shared/lib/date';
import { STATUS_BADGE } from '~/shared/lib/translateStatus';

import type { loader } from '~/routes/_protected.library._index';

const TABS = [
    { key: 'all',         label: '전체' },
    { key: 'completed',   label: '완료' },
    { key: 'pending',     label: '대기중' },
    { key: 'translating', label: '번역중' },
    { key: 'failed',      label: '실패' },
] as const;

const VALID_TABS = new Set(TABS.map((t) => t.key));

export function LibraryView() {
    const { items, total, page, size, currentTab, error } = useLoaderData<typeof loader>();
    const [searchParams, setSearchParams] = useSearchParams();

    const totalPages = Math.ceil(total / size) || 1;

    // 유효하지 않은 tab 또는 page 초과 → URL 정규화
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

    return (
        <div className="page-wrapper py-8">
            <div className="container-main">
                {/* 헤더 */}
                <div className="flex items-center justify-between mb-8">
                    <div>
                        <h1 className="text-[length:var(--text-page-title-mobile)] lg:text-[length:var(--text-page-title)] font-bold text-gray-900 mb-2">
                            라이브러리
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
                        <p className="text-gray-500 font-medium mb-1">번역 이력이 없습니다</p>
                        <p className="text-sm text-gray-400">새 번역 버튼을 눌러 고서 번역을 시작해보세요</p>
                    </div>
                ) : (
                    <div className="bg-white rounded-lg shadow-sm border border-gray-200 divide-y divide-gray-100">
                        {items.map((item) => {
                            const badge = STATUS_BADGE[item.status];
                            return (
                                <Link
                                    key={item.book_id}
                                    to={`/library/${item.book_id}`}
                                    className="flex items-center justify-between px-6 py-4 hover:bg-gray-50 transition-colors"
                                >
                                    <div className="flex items-center gap-3 min-w-0">
                                        <BookOpen className="w-5 h-5 text-gray-400 shrink-0" aria-hidden />
                                        <span className="text-gray-900 font-medium truncate">{item.title}</span>
                                    </div>
                                    <div className="flex items-center gap-4 ml-4 shrink-0">
                                        <span className={`text-xs font-medium px-2 py-1 rounded-full border ${badge.className}`}>
                                            {badge.label}
                                        </span>
                                        <span className="text-sm text-gray-400 hidden sm:block">
                                            {formatDate(item.created_at)}
                                        </span>
                                    </div>
                                </Link>
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
