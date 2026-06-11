import { PUBLIC_BASE_URL } from '~/shared/api/client';

import type { LearnPage } from '../types/workspace';

interface Props {
    sourceFileUrl: string | null;
    pages: LearnPage[];
}

export function OriginalPanel({ sourceFileUrl, pages }: Props) {
    return (
        <div className="flex flex-col gap-5">
            <div className="overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-sm">
                <div className="border-b border-gray-200 bg-gray-50 px-4 py-3 text-sm font-semibold text-gray-700">
                    원본 이미지
                </div>
                {sourceFileUrl ? (
                    <div className="max-h-[420px] overflow-y-auto bg-gray-50">
                        <img
                            src={`${PUBLIC_BASE_URL}${sourceFileUrl}`}
                            alt="고서 원문 이미지"
                            className="w-full object-contain"
                        />
                    </div>
                ) : (
                    <div className="flex h-40 items-center justify-center text-sm text-gray-400">
                        원문 이미지가 없습니다
                    </div>
                )}
            </div>

            <div className="overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-sm">
                <div className="border-b border-gray-200 bg-gray-50 px-4 py-3 text-sm font-semibold text-gray-700">
                    📜 OCR 원문
                </div>
                <div className="max-h-72 overflow-y-auto p-4">
                    {pages.map((page) => (
                        <div key={page.page_no}>
                            {pages.length > 1 && (
                                <p className="mb-1 text-xs font-semibold text-gray-400">
                                    p.{page.page_no}
                                </p>
                            )}
                            <pre className="whitespace-pre-wrap font-sans text-sm leading-relaxed break-words text-gray-800">
                                {page.ocr_text || '내용이 없습니다.'}
                            </pre>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
