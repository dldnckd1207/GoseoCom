import { Link, useLoaderData } from 'react-router';

import { ArrowLeft } from 'lucide-react';

import { BookAnalyzeSection } from '~/features/translate';
import { PUBLIC_BASE_URL } from '~/shared/api/client';
import { STATUS_BADGE } from '~/shared/lib/translateStatus';

import type { loader } from '~/routes/_layout.library.$id';

function textOrDash(value: string | null | undefined): string {
    return value?.trim() ? value : '-';
}

export function LibraryDetailView() {
    const { book } = useLoaderData<typeof loader>();
    const badge = STATUS_BADGE[book.status];
    const sortedPages = [...book.pages].sort((a, b) => a.page_no - b.page_no);

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
                        <h1 className="text-[length:var(--text-page-title-mobile)] lg:text-[length:var(--text-page-title)] font-bold text-gray-900 break-words min-w-0">
                            {book.title}
                        </h1>
                        <span className={`text-xs font-medium px-2 py-1 rounded-full border ${badge.className}`}>
                            {badge.label}
                        </span>
                    </div>
                    <p className="mt-1 text-sm text-gray-500">전체 {book.total_pages}페이지</p>
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

                {/* 번역 결과 */}
                {sortedPages.map((p) => (
                    <div key={p.page_no} className="bg-white rounded-lg shadow-sm border border-gray-200 mb-4 overflow-hidden">
                        <div className="bg-gray-50 border-b border-gray-200 px-6 py-3">
                            <span className="text-sm font-semibold text-gray-700">{p.page_no}페이지</span>
                        </div>
                        <div className="grid grid-cols-1 lg:grid-cols-3 divide-y lg:divide-y-0 lg:divide-x divide-gray-100">
                            <div className="px-6 py-4">
                                <p className="text-xs font-semibold text-gray-400 uppercase mb-2">OCR 원문</p>
                                <pre className="text-sm text-gray-700 whitespace-pre-wrap font-sans break-words">{textOrDash(p.ocr_text)}</pre>
                            </div>
                            <div className="px-6 py-4">
                                <p className="text-xs font-semibold text-gray-400 uppercase mb-2">직역</p>
                                <pre className="text-sm text-gray-700 whitespace-pre-wrap font-sans break-words">{textOrDash(p.literal_text)}</pre>
                            </div>
                            <div className="px-6 py-4">
                                <p className="text-xs font-semibold text-gray-400 uppercase mb-2">의역</p>
                                <pre className="text-sm text-gray-700 whitespace-pre-wrap font-sans break-words">{textOrDash(p.interpretive_text)}</pre>
                            </div>
                        </div>
                    </div>
                ))}

                {/* 분석 결과 */}
                <BookAnalyzeSection summaryText={book.summary_text} keywords={book.keywords} />
            </div>
        </div>
    );
}
