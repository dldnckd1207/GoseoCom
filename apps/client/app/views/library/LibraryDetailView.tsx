import { useState } from 'react';

import { Link, useLoaderData, useNavigate } from 'react-router';

import { ArrowLeft, Loader2, RefreshCw } from 'lucide-react';

import { ApiError, PUBLIC_BASE_URL, apiClient } from '~/shared/api/client';
import { API_ENDPOINTS } from '~/shared/api/endpoints';
import { STATUS_BADGE } from '~/shared/lib/translateStatus';

import type { loader } from '~/routes/_protected.library.$id';

function textOrDash(value: string | null | undefined): string {
    return value?.trim() ? value : '-';
}

export function LibraryDetailView() {
    const { book } = useLoaderData<typeof loader>();
    const navigate = useNavigate();
    const badge = STATUS_BADGE[book.status];
    const sortedPages = [...book.pages].sort((a, b) => a.page_no - b.page_no);

    const [retrying, setRetrying] = useState(false);
    const [retryError, setRetryError] = useState<string | null>(null);

    const handleRetry = async () => {
        setRetrying(true);
        setRetryError(null);
        try {
            await apiClient.post(API_ENDPOINTS.TRANSLATE_RETRY(book.book_id));
            navigate('/library');
        } catch (err) {
            if (err instanceof ApiError && err.code === 'NO_SOURCE_FILE') {
                setRetryError('이전 버전 번역이라 원본 파일이 없습니다. 새로 번역해주세요.');
            } else {
                setRetryError('재시도 요청에 실패했습니다. 잠시 후 다시 시도해주세요.');
            }
            setRetrying(false);
        }
    };

    return (
        <div className="page-wrapper py-8">
            <div className="container-main">
                {/* 뒤로가기 */}
                <Link
                    to="/library"
                    className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 mb-6 transition-colors"
                >
                    <ArrowLeft className="w-4 h-4" aria-hidden />
                    <span>라이브러리로 돌아가기</span>
                </Link>

                {/* 책 정보 */}
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 px-6 py-5 mb-6">
                    <div className="flex items-center gap-3 flex-wrap">
                        <h1 className="text-[length:var(--text-page-title-mobile)] lg:text-[length:var(--text-page-title)] font-bold text-gray-900">
                            {book.title}
                        </h1>
                        <span className={`text-xs font-medium px-2 py-1 rounded-full border ${badge.className}`}>
                            {badge.label}
                        </span>
                    </div>
                    {book.status !== 'FAILED' && (
                        <p className="mt-1 text-sm text-gray-500">전체 {book.total_pages}페이지</p>
                    )}
                </div>

                {/* 원본 이미지 */}
                {book.source_file_url && (
                    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
                        <p className="text-xs font-semibold text-gray-400 uppercase mb-3">원본 이미지</p>
                        <img
                            src={`${PUBLIC_BASE_URL}${book.source_file_url}`}
                            alt={book.title}
                            className="max-w-full max-h-96 object-contain rounded-md border border-gray-100"
                        />
                    </div>
                )}

                {/* FAILED */}
                {book.status === 'FAILED' && (
                    <div className="rounded-lg border border-red-200 bg-red-50 px-6 py-5 mb-6">
                        <div className="flex items-center justify-between flex-wrap gap-3">
                            <p className="text-red-700">처리 중 오류가 발생했습니다.</p>
                            <button
                                type="button"
                                onClick={handleRetry}
                                disabled={retrying}
                                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-60 disabled:cursor-not-allowed transition-colors shrink-0"
                            >
                                {retrying
                                    ? <Loader2 className="w-4 h-4 animate-spin" aria-hidden />
                                    : <RefreshCw className="w-4 h-4" aria-hidden />
                                }
                                <span>{retrying ? '재시도 중...' : '다시 번역하기'}</span>
                            </button>
                        </div>
                        {retryError && (
                            <div className="mt-3 flex items-center gap-3 flex-wrap">
                                <p className="text-sm text-red-600">{retryError}</p>
                                {retryError.includes('원본 파일') && (
                                    <Link
                                        to="/translate"
                                        className="text-sm font-medium text-blue-600 hover:underline shrink-0"
                                    >
                                        새로 번역하기 →
                                    </Link>
                                )}
                            </div>
                        )}
                    </div>
                )}

                {/* 번역 결과 */}
                {book.status === 'COMPLETED' && sortedPages.map((p) => (
                    <div key={p.page_no} className="bg-white rounded-lg shadow-sm border border-gray-200 mb-4 overflow-hidden">
                        <div className="bg-gray-50 border-b border-gray-200 px-6 py-3">
                            <span className="text-sm font-semibold text-gray-700">{p.page_no}페이지</span>
                        </div>
                        <div className="grid grid-cols-1 lg:grid-cols-3 divide-y lg:divide-y-0 lg:divide-x divide-gray-100">
                            <div className="px-6 py-4">
                                <p className="text-xs font-semibold text-gray-400 uppercase mb-2">OCR 원문</p>
                                <p className="text-sm text-gray-700 whitespace-pre-wrap">{textOrDash(p.ocr_text)}</p>
                            </div>
                            <div className="px-6 py-4">
                                <p className="text-xs font-semibold text-gray-400 uppercase mb-2">직역</p>
                                <p className="text-sm text-gray-700 whitespace-pre-wrap">{textOrDash(p.literal_text)}</p>
                            </div>
                            <div className="px-6 py-4">
                                <p className="text-xs font-semibold text-gray-400 uppercase mb-2">의역</p>
                                <p className="text-sm text-gray-700 whitespace-pre-wrap">{textOrDash(p.interpretive_text)}</p>
                            </div>
                        </div>
                    </div>
                ))}

                {/* 처리 중 */}
                {(book.status === 'PENDING' || book.status === 'OCR_PROCESSING' || book.status === 'TRANSLATING') && (
                    <div className="rounded-lg border border-blue-200 bg-blue-50 px-6 py-5 text-blue-700">
                        번역이 처리 중입니다. 잠시 후 다시 확인해주세요.
                    </div>
                )}
            </div>
        </div>
    );
}
