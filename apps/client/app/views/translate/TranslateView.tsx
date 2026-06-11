import { useEffect, useRef, useState } from 'react';

import { Link, useFetcher, useLoaderData } from 'react-router';

import { Check, Loader2, Pencil, Sparkles, Upload } from 'lucide-react';

import { ApiError, apiClient } from '~/shared/api/client';
import { API_ENDPOINTS } from '~/shared/api/endpoints';

import type { loader, action } from '~/routes/_protected.translate';
import type { BookResult, BookStatus } from '~/shared/types/translate';

type TranslateStep =
    | { step: 'idle' }
    | { step: 'ocr_done'; bookId: string; ocrText: string }
    | { step: 'translating'; bookId: string }
    | { step: 'done'; bookId: string; literal: string; interpretive: string };

type ActiveTab = 'literal' | 'interpretive';

const POLL_INTERVAL = 3000;
const MAX_FILE_SIZE = 10 * 1024 * 1024;

const OCR_PROCESSING_STATUSES = new Set<BookStatus>(['PENDING', 'OCR_PROCESSING']);
const TRANSLATE_PROCESSING_STATUSES = new Set<BookStatus>(['PENDING', 'TRANSLATING']);

export function TranslateView() {
    const { initialBook } = useLoaderData<typeof loader>();

    const initialOcrText = initialBook?.pages[0]?.ocr_text ?? '';
    const initialStage: TranslateStep = initialBook
        ? { step: 'ocr_done', bookId: initialBook.book_id, ocrText: initialOcrText }
        : { step: 'idle' };
    const initialTitle = initialBook?.title ?? '';

    const [fetcherKey, setFetcherKey] = useState('translate-0');
    const fetcher = useFetcher<typeof action>({ key: fetcherKey });

    const [stage, setStage] = useState<TranslateStep>(initialStage);
    const [bookTitle, setBookTitle] = useState(initialTitle);
    const [ocrText, setOcrText] = useState(initialOcrText);
    const [fileError, setFileError] = useState<string | null>(null);
    const [translateError, setTranslateError] = useState<string | null>(null);
    const [activeTab, setActiveTab] = useState<ActiveTab>('literal');
    const fileInputRef = useRef<HTMLInputElement>(null);
    // 번역 실패 시 이전 OCR 상태로 복구하기 위한 ref
    const prevOcrStateRef = useRef<{ bookId: string; ocrText: string } | null>(null);

    const bookId = fetcher.state === 'idle' && fetcher.data?.ok === true
        ? fetcher.data.bookId
        : null;

    // OCR 폴링 — bookId가 생기고 stage가 idle일 때 실행
    const isOcrPolling = !!bookId && stage.step === 'idle';

    useEffect(() => {
        if (!bookId || stage.step !== 'idle') return;

        let cancelled = false;
        let timeoutId: ReturnType<typeof setTimeout> | null = null;

        const poll = async () => {
            try {
                const data = await apiClient.get<BookResult>(API_ENDPOINTS.TRANSLATE_DETAIL(bookId));
                if (cancelled) return;

                if (data.status === 'OCR_COMPLETED') {
                    const text = data.pages[0]?.ocr_text ?? '';
                    setOcrText(text);
                    setBookTitle(data.title);
                    setStage({ step: 'ocr_done', bookId, ocrText: text });
                    return;
                }
                if (data.status === 'COMPLETED') {
                    setOcrText('');
                    setBookTitle(data.title);
                    setStage({ step: 'ocr_done', bookId, ocrText: '' });
                    return;
                }
                if (data.status === 'FAILED') {
                    setFileError('이미지 인식에 실패했습니다.');
                    setStage({ step: 'idle' });
                    return;
                }
                if (OCR_PROCESSING_STATUSES.has(data.status)) {
                    timeoutId = setTimeout(poll, POLL_INTERVAL);
                }
            } catch {
                if (!cancelled) {
                    setFileError('이미지 인식 중 오류가 발생했습니다.');
                    setStage({ step: 'idle' });
                }
            }
        };

        poll();
        return () => {
            cancelled = true;
            if (timeoutId) clearTimeout(timeoutId);
        };
    }, [bookId, stage.step]);

    // 번역 폴링 — translating 상태일 때 useEffect로 실행 (언마운트 시 정리 보장)
    const translatingBookId = stage.step === 'translating' ? stage.bookId : null;

    useEffect(() => {
        if (!translatingBookId) return;

        let cancelled = false;
        let timeoutId: ReturnType<typeof setTimeout> | null = null;

        const poll = async () => {
            try {
                const data = await apiClient.get<BookResult>(
                    API_ENDPOINTS.TRANSLATE_DETAIL(translatingBookId),
                );
                if (cancelled) return;

                if (data.status === 'COMPLETED') {
                    setBookTitle(data.title);
                    setStage({
                        step: 'done',
                        bookId: translatingBookId,
                        literal: data.pages[0]?.literal_text ?? '',
                        interpretive: data.pages[0]?.interpretive_text ?? '',
                    });
                    return;
                }
                if (data.status === 'FAILED') {
                    setTranslateError('번역에 실패했습니다.');
                    const prev = prevOcrStateRef.current;
                    setStage(prev ? { step: 'ocr_done', ...prev } : { step: 'idle' });
                    return;
                }
                if (TRANSLATE_PROCESSING_STATUSES.has(data.status)) {
                    timeoutId = setTimeout(poll, POLL_INTERVAL);
                }
            } catch {
                if (!cancelled) {
                    setTranslateError('번역 결과를 가져오는 중 오류가 발생했습니다.');
                    const prev = prevOcrStateRef.current;
                    setStage(prev ? { step: 'ocr_done', ...prev } : { step: 'idle' });
                }
            }
        };

        poll();
        return () => {
            cancelled = true;
            if (timeoutId) clearTimeout(timeoutId);
        };
    }, [translatingBookId]);

    // AI 번역 실행 — API 호출만, 폴링은 useEffect에서
    const handleTranslate = async () => {
        if (!ocrText.trim()) return;

        const currentBookId = stage.step === 'ocr_done' ? stage.bookId : undefined;
        prevOcrStateRef.current = currentBookId ? { bookId: currentBookId, ocrText } : null;
        setTranslateError(null);

        try {
            const res = await apiClient.post<{ book_id: string }>(
                API_ENDPOINTS.TRANSLATE_TEXT,
                { text: ocrText, book_id: currentBookId ?? null },
            );
            setStage({ step: 'translating', bookId: res.book_id });
        } catch (err) {
            setTranslateError(err instanceof ApiError ? err.message : '번역 시작에 실패했습니다.');
        }
    };

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        e.target.value = '';
        if (!file) return;

        if (!file.type.startsWith('image/')) {
            setFileError('이미지 파일만 업로드할 수 있습니다.');
            return;
        }
        if (file.size > MAX_FILE_SIZE) {
            setFileError('파일 크기는 10MB를 초과할 수 없습니다.');
            return;
        }

        setFileError(null);
        setTranslateError(null);
        setOcrText('');
        setStage({ step: 'idle' });
        // fetcherKey는 바꾸지 않음 — 키를 바꾸면 submit 후 새 키 fetcher로 전환되어
        // action 응답(bookId)을 수신 못하고 OCR 폴링이 시작되지 않음
        const fd = new FormData();
        fd.append('file', file);
        fetcher.submit(fd, { method: 'post', encType: 'multipart/form-data' });
    };

    const handleReset = () => {
        setStage({ step: 'idle' });
        setBookTitle('');
        setOcrText('');
        setFileError(null);
        setTranslateError(null);
        setFetcherKey(`translate-${Date.now()}`);
        prevOcrStateRef.current = null;
    };

    const [editingTitle, setEditingTitle] = useState(false);
    const [titleValue, setTitleValue] = useState('');
    const [titleSaved, setTitleSaved] = useState(false);
    const titleInputRef = useRef<HTMLInputElement>(null);

    const currentBookId = stage.step !== 'idle' ? stage.bookId : null;

    useEffect(() => {
        setTitleValue(bookTitle);
    }, [bookTitle]);

    useEffect(() => {
        if (editingTitle) titleInputRef.current?.select();
    }, [editingTitle]);

    const handleTitleSave = async () => {
        if (!currentBookId) { setEditingTitle(false); return; }
        const trimmed = titleValue.trim();
        if (!trimmed) {
            setTitleValue(bookTitle);
            setEditingTitle(false);
            return;
        }
        if (trimmed === bookTitle) { setEditingTitle(false); return; }
        try {
            await apiClient.put(API_ENDPOINTS.TRANSLATE_TITLE_UPDATE(currentBookId), { title: trimmed });
            setBookTitle(trimmed);
            setTitleSaved(true);
            setEditingTitle(false);
            setTimeout(() => setTitleSaved(false), 800);
        } catch {
            setTitleValue(bookTitle);
            setEditingTitle(false);
        }
    };

    const isUploading = fetcher.state !== 'idle';
    const isOcrLoading = isOcrPolling;
    const isTranslating = stage.step === 'translating';
    const uploadDisabled = isUploading || isOcrLoading || isTranslating;

    const fetcherError = fetcher.data?.ok === false
        ? (fetcher.data.error ?? '오류가 발생했습니다.')
        : null;
    const isRateLimited = fetcher.data?.ok === false && fetcher.data.errorCode === 'DAILY_LIMIT_EXCEEDED';

    const showEditor = stage.step !== 'idle' || isOcrPolling;
    const translateDisabled = !ocrText.trim() || isTranslating || isOcrLoading || isUploading;

    return (
        <div className="page-wrapper py-8">
            <div className="container-main">
                <div className="mb-6">
                    <h1 className="mb-2 text-[length:var(--text-page-title-mobile)] font-bold text-gray-900 lg:text-[length:var(--text-page-title)]">고서 번역</h1>
                    <p className="text-gray-600">AI 기반 자동 번역으로 고서를 현대 한국어로 변환하세요</p>
                </div>

                {/* 번역 제목 — OCR 완료 후 표시 */}
                {bookTitle && (
                    <div className="mb-4 flex items-center gap-2 rounded-lg border border-gray-200 bg-white px-4 py-3 shadow-sm">
                        {editingTitle ? (
                            <input
                                ref={titleInputRef}
                                type="text"
                                value={titleValue}
                                onChange={(e) => setTitleValue(e.target.value)}
                                onBlur={handleTitleSave}
                                onKeyDown={(e) => {
                                    if (e.key === 'Enter') handleTitleSave();
                                    if (e.key === 'Escape') {
                                        setTitleValue(bookTitle);
                                        setEditingTitle(false);
                                    }
                                }}
                                className="flex-1 border-b-2 border-blue-500 bg-transparent text-sm font-medium text-gray-800 outline-none"
                            />
                        ) : (
                            <button
                                type="button"
                                onClick={() => setEditingTitle(true)}
                                className="flex flex-1 items-center gap-2 text-left text-sm font-medium text-gray-800 hover:text-gray-900 transition-colors min-w-0"
                            >
                                {titleSaved
                                    ? <Check className="w-4 h-4 text-green-500 shrink-0" aria-hidden />
                                    : <Pencil className="w-4 h-4 text-gray-400 shrink-0" aria-hidden />
                                }
                                <span className="truncate">{bookTitle}</span>
                            </button>
                        )}
                    </div>
                )}

                {/* 이미지 업로드 */}
                <div className="mb-4 rounded-lg border border-gray-200 bg-white shadow-sm p-4">
                    <label className={`flex items-center justify-center gap-3 w-full border-2 border-dashed rounded-lg p-6 text-center transition-colors ${uploadDisabled ? 'border-gray-200 opacity-50 cursor-not-allowed' : 'border-gray-300 cursor-pointer hover:border-blue-400'}`}>
                        <input
                            ref={fileInputRef}
                            type="file"
                            accept="image/*"
                            disabled={uploadDisabled}
                            onChange={handleFileChange}
                            className="sr-only"
                            aria-label="고서 이미지 업로드"
                        />
                        {(isUploading || isOcrLoading) ? (
                            <>
                                <Loader2 className="w-6 h-6 text-blue-500 animate-spin shrink-0" aria-hidden />
                                <span className="font-medium text-gray-700">
                                    {isUploading ? '업로드 중...' : '이미지 인식 중...'}
                                </span>
                            </>
                        ) : (
                            <>
                                <Upload className="w-6 h-6 text-gray-400 shrink-0" aria-hidden />
                                <span className="font-medium text-gray-700">
                                    이미지를 드래그하거나 클릭하여 업로드 — PNG, JPG (최대 10MB)
                                </span>
                            </>
                        )}
                    </label>
                    {fileError && <p className="mt-2 text-sm text-red-500">{fileError}</p>}
                    {fetcherError && (
                        <div className="mt-2 flex items-center justify-between gap-3">
                            <p className="text-sm text-red-500">{fetcherError}</p>
                            {isRateLimited && (
                                <Link to="/history" className="shrink-0 text-sm font-medium text-blue-600 hover:underline">
                                    번역 이력 보기 →
                                </Link>
                            )}
                        </div>
                    )}
                </div>

                {/* 원문 + 번역 결과 2열 */}
                <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
                    {/* 좌: 원문 */}
                    <div className="rounded-lg border border-gray-200 bg-white shadow-sm overflow-hidden">
                        <div className="flex items-center justify-between border-b border-gray-200 bg-gray-50 px-4 py-3">
                            <span className="text-sm font-semibold text-gray-700">원문</span>
                            <button
                                type="button"
                                onClick={handleTranslate}
                                disabled={translateDisabled}
                                className="flex items-center gap-1.5 rounded-md bg-blue-600 px-3 py-1.5 text-sm font-medium text-white transition-colors hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                {isTranslating
                                    ? <><Loader2 className="w-3.5 h-3.5 animate-spin" aria-hidden />번역 중...</>
                                    : <><Sparkles className="w-3.5 h-3.5" aria-hidden />AI 번역</>
                                }
                            </button>
                        </div>
                        <textarea
                            value={ocrText}
                            onChange={(e) => setOcrText(e.target.value)}
                            disabled={isTranslating || isOcrLoading || isUploading}
                            placeholder={isOcrLoading || isUploading
                                ? '이미지를 인식하는 중입니다...'
                                : '번역할 원문을 입력하거나 이미지를 업로드하세요'}
                            className="w-full resize-none p-4 text-sm text-gray-800 placeholder:text-gray-400 focus:outline-none disabled:bg-gray-50 disabled:cursor-not-allowed"
                            rows={14}
                        />
                        {translateError && (
                            <p className="px-4 pb-3 text-sm text-red-500">{translateError}</p>
                        )}
                    </div>

                    {/* 우: 번역 결과 */}
                    <div className="rounded-lg border border-gray-200 bg-white shadow-sm overflow-hidden">
                        <div className="flex items-center border-b border-gray-200 bg-gray-50 px-4 py-3 gap-2">
                            {(['literal', 'interpretive'] as const).map((tab) => (
                                <button
                                    key={tab}
                                    type="button"
                                    onClick={() => setActiveTab(tab)}
                                    className={`px-3 py-1 text-sm font-medium rounded-md transition-colors ${activeTab === tab ? 'bg-blue-600 text-white' : 'text-gray-600 hover:text-gray-900'}`}
                                >
                                    {tab === 'literal' ? '직역' : '의역'}
                                </button>
                            ))}
                        </div>
                        <div className="p-4 min-h-[13.5rem]">
                            {stage.step === 'done' ? (
                                <pre className="text-sm leading-relaxed text-gray-800 whitespace-pre-wrap font-sans break-words">
                                    {activeTab === 'literal' ? stage.literal : stage.interpretive}
                                </pre>
                            ) : isTranslating ? (
                                <div className="flex h-32 items-center justify-center gap-2 text-gray-400">
                                    <Loader2 className="w-5 h-5 animate-spin" aria-hidden />
                                    <span className="text-sm">번역 중...</span>
                                </div>
                            ) : (
                                <p className="text-sm text-gray-400">
                                    {showEditor
                                        ? 'AI 번역 버튼을 클릭하면 결과가 여기에 표시됩니다.'
                                        : '원문을 입력하거나 이미지를 업로드 후 AI 번역을 실행하세요.'}
                                </p>
                            )}
                        </div>
                    </div>
                </div>

                {/* 완료 후 액션 */}
                {stage.step === 'done' && (
                    <div className="mt-4 flex items-center justify-center gap-3">
                        <Link
                            to={`/history/${stage.bookId}`}
                            className="px-6 py-2 text-sm font-medium text-white rounded-lg bg-blue-600 hover:bg-blue-700 transition-colors"
                        >
                            번역 이력 보기
                        </Link>
                        <button
                            type="button"
                            onClick={handleReset}
                            className="px-6 py-2 text-sm font-medium text-blue-600 rounded-lg border border-blue-600 hover:bg-blue-50 transition-colors"
                        >
                            새로 번역하기
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
}
