import { useEffect, useState } from 'react';

import { Link, useLoaderData, useRevalidator, useSearchParams } from 'react-router';

import { BookOpen, ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight, Star } from 'lucide-react';

import { apiClient, PUBLIC_BASE_URL } from '~/shared/api/client';
import { API_ENDPOINTS } from '~/shared/api/endpoints';
import { formatDate } from '~/shared/lib/date';
import { useAuthStore } from '~/shared/stores/authStore';

import type { loader } from '~/routes/_layout.library._index';

export function LibraryView() {
    const { items, total, page, size, q, bm, error } = useLoaderData<typeof loader>();
    const [, setSearchParams] = useSearchParams();
    const revalidator = useRevalidator();
    const user = useAuthStore((s) => s.user);
    const isLoggedIn = user !== null;

    const totalPages = Math.ceil(total / size) || 1;

    // 북마크 낙관적 업데이트
    const [pendingBmId, setPendingBmId] = useState<string | null>(null);
    const [optimisticBm, setOptimisticBm] = useState<Record<string, boolean>>({});

    // 검색창 입력 상태
    const [searchInput, setSearchInput] = useState(q);

    useEffect(() => {
        setSearchInput(q);
    }, [q]);

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

    const handleBmFilter = () => {
        setSearchParams(prev => {
            const next = new URLSearchParams(prev);
            if (bm) next.delete('bm');
            else next.set('bm', '1');
            next.delete('page');
            return next;
        });
    };

    const handlePageChange = (newPage: number) => {
        setSearchParams(prev => {
            const next = new URLSearchParams(prev);
            if (newPage === 1) next.delete('page');
            else next.set('page', String(newPage));
            return next;
        });
    };

    const handleBookmark = async (e: React.MouseEvent, bookId: string, currentBm: boolean) => {
        e.preventDefault();
        if (pendingBmId) return;
        setPendingBmId(bookId);
        setOptimisticBm(prev => ({ ...prev, [bookId]: !currentBm }));
        try {
            await apiClient.put(API_ENDPOINTS.TRANSLATE_BOOKMARK(bookId), {});
            await revalidator.revalidate();
            setOptimisticBm(prev => { const next = { ...prev }; delete next[bookId]; return next; });
        } catch {
            setOptimisticBm(prev => ({ ...prev, [bookId]: currentBm }));
        } finally {
            setPendingBmId(null);
        }
    };

    return (
        <div className="page-wrapper py-8">
            <div className="container-main">
                {/* 헤더 */}
                <div className="mb-6">
                    <h1 className="text-[length:var(--text-page-title-mobile)] lg:text-[length:var(--text-page-title)] font-bold text-gray-900 mb-2">
                        라이브러리
                    </h1>
                    <p className="text-gray-600">다양한 고서 번역 결과를 탐색하세요</p>
                </div>

                {/* 검색 + 북마크 필터 */}
                <div className="flex items-center gap-3 mb-6">
                    <div className="relative flex-1">
                        <input
                            type="text"
                            value={searchInput}
                            onChange={(e) => setSearchInput(e.target.value)}
                            placeholder="제목 검색..."
                            className="w-full rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm text-gray-800 placeholder:text-gray-400 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                        />
                    </div>
                    {isLoggedIn && (
                        <button
                            type="button"
                            onClick={handleBmFilter}
                            className={`flex items-center gap-1.5 rounded-lg border px-3 py-2 text-sm font-medium transition-colors whitespace-nowrap ${
                                bm
                                    ? 'border-yellow-400 bg-yellow-50 text-yellow-700'
                                    : 'border-gray-300 bg-white text-gray-600 hover:border-gray-400'
                            }`}
                        >
                            <Star className={`w-4 h-4 ${bm ? 'fill-yellow-400 text-yellow-400' : ''}`} aria-hidden />
                            북마크
                        </button>
                    )}
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
                            {q || bm ? '검색 결과가 없습니다' : '아직 등록된 번역 결과가 없습니다'}
                        </p>
                        <p className="text-sm text-gray-400">
                            {q || bm ? '다른 검색어나 필터를 시도해보세요' : '번역이 완료되면 이곳에 표시됩니다'}
                        </p>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {items.map((item) => {
                            const isBm = optimisticBm[item.book_id] ?? item.is_bookmarked;
                            const isPending = pendingBmId === item.book_id;
                            const isOwn = user?.user_id === item.owner_user_id;
                            return (
                                <div
                                    key={item.book_id}
                                    className="bg-white rounded-lg border border-gray-200 overflow-hidden hover:shadow-md transition-shadow group relative"
                                >
                                    {/* 북마크 버튼 — 로그인 + 타인 Book만 */}
                                    {isLoggedIn && !isOwn && (
                                        <button
                                            type="button"
                                            onClick={(e) => handleBookmark(e, item.book_id, item.is_bookmarked)}
                                            disabled={isPending}
                                            aria-pressed={isBm}
                                            aria-label={isBm ? '북마크 해제' : '북마크 추가'}
                                            className="absolute top-2 right-2 z-10 p-1.5 rounded-md bg-white/80 backdrop-blur-sm transition-colors hover:bg-white disabled:opacity-50"
                                        >
                                            <Star
                                                className={`w-4 h-4 transition-colors ${
                                                    isBm ? 'fill-yellow-400 text-yellow-400' : 'text-gray-400 hover:text-yellow-400'
                                                }`}
                                                aria-hidden
                                            />
                                        </button>
                                    )}

                                    <Link
                                        to={`/library/${item.book_id}`}
                                        className="block"
                                    >
                                        {/* 썸네일 */}
                                        <div className="bg-gray-50 border-b border-gray-100 h-36 flex items-center justify-center overflow-hidden">
                                            {item.source_file_url ? (
                                                <img
                                                    src={`${PUBLIC_BASE_URL}${item.source_file_url}`}
                                                    alt={item.title}
                                                    className="w-full h-full object-cover"
                                                />
                                            ) : (
                                                <BookOpen className="w-10 h-10 text-gray-300" aria-hidden />
                                            )}
                                        </div>

                                        {/* 카드 바디 */}
                                        <div className="p-4">
                                            <h3 className="text-sm font-semibold text-gray-900 line-clamp-2 break-words mb-2 group-hover:text-blue-600 transition-colors">
                                                {item.title}
                                            </h3>
                                            <div className="flex items-center justify-between">
                                                <div className="flex flex-col gap-0.5">
                                                    <span className="text-xs text-gray-400">{formatDate(item.created_at)}</span>
                                                    {item.owner_name && (
                                                        <span className="text-xs text-gray-400">{item.owner_name}</span>
                                                    )}
                                                </div>
                                                <span className="text-xs font-medium text-blue-600 group-hover:text-blue-700">
                                                    자세히 보기 →
                                                </span>
                                            </div>
                                        </div>
                                    </Link>
                                </div>
                            );
                        })}
                    </div>
                )}

                {/* 페이지네이션 */}
                {totalPages > 1 && (
                    <div className="flex justify-center items-center gap-1 mt-8">
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
