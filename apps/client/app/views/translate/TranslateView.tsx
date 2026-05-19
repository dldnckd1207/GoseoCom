import { useEffect, useRef, useState } from 'react';

import { Link, useFetcher } from 'react-router';

import { Loader2, Sparkles, Upload } from 'lucide-react';

import { apiClient } from '~/shared/api/client';
import { API_ENDPOINTS } from '~/shared/api/endpoints';

import type { action } from '~/routes/_protected.translate';
import type { BookResult, BookStatus } from '~/shared/types/translate';

type Phase = 'idle' | 'uploading' | 'translating' | 'completed' | 'failed' | 'no_text';

const POLL_INTERVAL = 3000;
const MAX_FILE_SIZE = 10 * 1024 * 1024;

const PROCESSING_LABEL: Partial<Record<BookStatus, string>> = {
    PENDING: '번역 준비 중...',
    OCR_PROCESSING: '이미지 인식 중...',
    TRANSLATING: '번역 중...',
};

export function TranslateView() {
    // fetcher key를 교체해 이전 action data가 재시도 상태에 섞이지 않도록 한다
    const [fetcherKey, setFetcherKey] = useState('translate-0');
    const fetcher = useFetcher<typeof action>({ key: fetcherKey });
    const [result, setResult] = useState<BookResult | null>(null);
    const [pollingStatus, setPollingStatus] = useState<BookStatus | null>(null);
    const [pollingError, setPollingError] = useState<string | null>(null);
    const [fileError, setFileError] = useState<string | null>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    // bookId — 현재 fetcher에서 derive (key 교체 시 자동으로 null)
    const bookId = fetcher.state === 'idle' && fetcher.data?.ok === true
        ? fetcher.data.bookId
        : null;

    // phase — 완전 derived
    const phase: Phase = (() => {
        if (fetcher.state !== 'idle') return 'uploading';
        if (fetcher.data?.ok === false) return 'failed';
        if (!bookId) return 'idle';
        if (pollingError) return 'failed';
        if (result) return result.pages.some((p) => p.status === 'NO_TEXT') ? 'no_text' : 'completed';
        return 'translating';
    })();

    // 폴링 — setTimeout 재귀, 중간 상태(OCR_PROCESSING/TRANSLATING) 저장
    useEffect(() => {
        if (!bookId) return;

        let cancelled = false;
        let timeoutId: ReturnType<typeof setTimeout> | null = null;

        const poll = async () => {
            try {
                const data = await apiClient.get<BookResult>(API_ENDPOINTS.TRANSLATE_DETAIL(bookId));
                if (cancelled) return;

                setPollingStatus(data.status);

                if (data.status === 'COMPLETED') {
                    setResult(data);
                    return;
                }
                if (data.status === 'FAILED') {
                    setPollingError('번역에 실패했습니다.');
                    return;
                }
                timeoutId = setTimeout(poll, POLL_INTERVAL);
            } catch {
                if (!cancelled) setPollingError('번역 결과를 가져오는 중 오류가 발생했습니다.');
            }
        };

        poll();

        return () => {
            cancelled = true;
            if (timeoutId) clearTimeout(timeoutId);
        };
    }, [bookId]);

    const resetState = () => {
        setResult(null);
        setPollingStatus(null);
        setPollingError(null);
        setFileError(null);
    };

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        e.target.value = '';
        if (!file) return;

        if (!file.type.startsWith('image/')) {
            resetState();
            setFetcherKey(`translate-${Date.now()}`);
            setFileError('이미지 파일만 업로드할 수 있습니다.');
            return;
        }
        if (file.size > MAX_FILE_SIZE) {
            resetState();
            setFetcherKey(`translate-${Date.now()}`);
            setFileError('파일 크기는 10MB를 초과할 수 없습니다.');
            return;
        }

        resetState();
        const fd = new FormData();
        fd.append('file', file);
        fetcher.submit(fd, { method: 'post', encType: 'multipart/form-data' });
    };

    const handleRetry = () => {
        resetState();
        setFetcherKey(`translate-${Date.now()}`);
        fileInputRef.current?.click();
    };

    const isProcessing = phase === 'uploading' || phase === 'translating';
    const processingLabel = phase === 'uploading'
        ? '업로드 및 번역 준비 중...'
        : (pollingStatus ? (PROCESSING_LABEL[pollingStatus] ?? '번역 중...') : '번역 중...');
    const errorMessage = fetcher.data?.ok === false
        ? (fetcher.data.error ?? '오류가 발생했습니다.')
        : pollingError;
    const isRateLimited = fetcher.data?.ok === false && fetcher.data.errorCode === 'DAILY_LIMIT_EXCEEDED';

    return (
        <div className="page-wrapper py-8">
            <div className="container-main">
                <div className="mb-8">
                    <h1 className="mb-2 text-[length:var(--text-page-title-mobile)] font-bold text-gray-900 lg:text-[length:var(--text-page-title)]">고서 번역</h1>
                    <p className="text-gray-600">AI 기반 자동 번역으로 고서를 현대 한국어로 변환하세요</p>
                </div>

                {/* 파일 업로드 */}
                <div className="p-6 mb-6 rounded-lg border border-gray-200 bg-white shadow-sm">
                    <h2 className="mb-4 text-lg font-semibold text-gray-900">이미지 업로드</h2>
                    <label className={`block w-full border-2 border-dashed rounded-lg p-8 text-center transition-colors ${isProcessing ? 'border-gray-200 opacity-50 cursor-not-allowed' : 'border-gray-300 cursor-pointer hover:border-blue-400'}`}>
                        <input
                            ref={fileInputRef}
                            type="file"
                            accept="image/*"
                            disabled={isProcessing}
                            onChange={handleFileChange}
                            className="sr-only"
                            aria-label="고서 이미지 업로드"
                        />
                        <div className="flex flex-col items-center">
                            {isProcessing ? (
                                <>
                                    <Loader2 className="w-12 h-12 mb-3 text-blue-500 animate-spin" aria-hidden />
                                    <p className="font-medium text-gray-700">{processingLabel}</p>
                                </>
                            ) : (
                                <>
                                    <Upload className="w-12 h-12 mb-3 text-gray-400" aria-hidden />
                                    <p className="mb-1 font-medium text-gray-700">클릭하여 이미지를 업로드하세요</p>
                                    <p className="text-sm text-gray-500">PNG, JPG 등 이미지 파일 (최대 10MB)</p>
                                </>
                            )}
                        </div>
                    </label>
                    {fileError && (
                        <p className="mt-3 text-sm text-red-500">{fileError}</p>
                    )}
                </div>

                {/* 실패 / NO_TEXT / 한도초과 안내 */}
                {(phase === 'failed' || phase === 'no_text') && (
                    <div className={`flex flex-col gap-4 rounded-lg border p-6 mb-6 sm:flex-row sm:items-center sm:justify-between ${phase === 'no_text' ? 'border-amber-200 bg-amber-50' : 'border-red-200 bg-red-50'}`}>
                        <p className={`font-medium ${phase === 'no_text' ? 'text-amber-800' : 'text-red-700'}`}>
                            {phase === 'no_text'
                                ? '이미지에서 텍스트를 인식하지 못했습니다. 다른 이미지를 시도해보세요.'
                                : (errorMessage ?? '번역에 실패했습니다. 다시 시도해주세요.')}
                        </p>
                        {isRateLimited ? (
                            <Link
                                to="/library"
                                className="px-4 py-2 text-sm font-medium text-white rounded-lg bg-blue-600 hover:bg-blue-700 transition-colors shrink-0 text-center"
                            >
                                라이브러리 보기
                            </Link>
                        ) : (
                            <button
                                type="button"
                                onClick={handleRetry}
                                className="px-4 py-2 text-sm font-medium text-white rounded-lg bg-blue-600 hover:bg-blue-700 transition-colors shrink-0"
                            >
                                다시 시도
                            </button>
                        )}
                    </div>
                )}

                {/* 번역 결과 */}
                {phase === 'completed' && result && (
                    <>
                        <div className="grid grid-cols-1 gap-6 mb-6 lg:grid-cols-2">
                            <div className="overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm">
                                <div className="border-b border-gray-200 px-6 py-4 bg-gray-50">
                                    <h2 className="text-lg font-semibold text-gray-900">직역</h2>
                                </div>
                                <div className="p-6">
                                    <p className="leading-relaxed text-gray-800 whitespace-pre-wrap">
                                        {result.pages[0]?.literal_text ?? '—'}
                                    </p>
                                </div>
                            </div>
                            <div className="overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm">
                                <div className="border-b border-gray-200 px-6 py-4 bg-gray-50">
                                    <div className="flex items-center gap-2">
                                        <Sparkles className="w-5 h-5 text-blue-600" aria-hidden />
                                        <h2 className="text-lg font-semibold text-gray-900">의역</h2>
                                    </div>
                                </div>
                                <div className="p-6">
                                    <p className="leading-relaxed text-gray-800 whitespace-pre-wrap">
                                        {result.pages[0]?.interpretive_text ?? '—'}
                                    </p>
                                </div>
                            </div>
                        </div>
                        <div className="flex justify-center mb-6">
                            <button
                                type="button"
                                onClick={handleRetry}
                                className="px-6 py-2 text-sm font-medium text-blue-600 rounded-lg border border-blue-600 hover:bg-blue-50 transition-colors"
                            >
                                새 이미지로 번역하기
                            </button>
                        </div>
                    </>
                )}

                {/* 사용 안내 */}
                <div className="rounded-lg border border-blue-200 bg-blue-50 p-6">
                    <h3 className="mb-3 text-lg font-semibold text-blue-900">사용 안내</h3>
                    <ul className="space-y-2 text-blue-800">
                        <li className="flex items-start gap-2">
                            <span className="mt-1 text-blue-600" aria-hidden>•</span>
                            <span>고서 이미지를 업로드하면 AI가 자동으로 텍스트를 인식하고 번역합니다</span>
                        </li>
                        <li className="flex items-start gap-2">
                            <span className="mt-1 text-blue-600" aria-hidden>•</span>
                            <span>직역(원문에 충실한 번역)과 의역(현대 한국어로 자연스럽게 풀어쓴 번역)을 함께 제공합니다</span>
                        </li>
                        <li className="flex items-start gap-2">
                            <span className="mt-1 text-blue-600" aria-hidden>•</span>
                            <span>PNG, JPG 등 이미지 파일을 지원합니다 (최대 10MB)</span>
                        </li>
                    </ul>
                </div>
            </div>
        </div>
    );
}
