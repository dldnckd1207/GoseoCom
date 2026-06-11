import { useRef, useState } from 'react';

import { Link, useLoaderData, useNavigate } from 'react-router';

import { ArrowLeft, Loader2, Pencil, RefreshCw, Save } from 'lucide-react';

import { BookAnalyzeSection } from '~/features/translate';
import { ApiError, PUBLIC_BASE_URL, apiClient } from '~/shared/api/client';
import { API_ENDPOINTS } from '~/shared/api/endpoints';
import { STATUS_BADGE } from '~/shared/lib/translateStatus';

import type { loader } from '~/routes/_protected.history.$id';

type ActiveTab = 'literal' | 'interpretive';

export function HistoryDetailView() {
    const { book } = useLoaderData<typeof loader>();
    const navigate = useNavigate();
    const badge = STATUS_BADGE[book.status];
    const sortedPages = [...book.pages].sort((a, b) => a.page_no - b.page_no);

    const [retrying, setRetrying] = useState(false);
    const [retryError, setRetryError] = useState<string | null>(null);

    // 제목 편집
    const [title, setTitle] = useState(book.title);
    const [editingTitle, setEditingTitle] = useState(false);
    const [savingTitle, setSavingTitle] = useState(false);
    const titleInputRef = useRef<HTMLInputElement>(null);

    const handleTitleEdit = () => {
        setEditingTitle(true);
        setTimeout(() => titleInputRef.current?.select(), 0);
    };

    const handleTitleSave = async () => {
        const trimmed = title.trim();
        if (!trimmed) { setTitle(book.title); setEditingTitle(false); return; }
        if (trimmed === book.title) { setEditingTitle(false); return; }
        setSavingTitle(true);
        try {
            await apiClient.put(API_ENDPOINTS.TRANSLATE_TITLE_UPDATE(book.book_id), { title: trimmed });
            setTitle(trimmed);
        } catch {
            setTitle(book.title);
        } finally {
            setSavingTitle(false);
            setEditingTitle(false);
        }
    };

    const handleTitleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
        if (e.key === 'Enter') handleTitleSave();
        if (e.key === 'Escape') { setTitle(book.title); setEditingTitle(false); }
    };

    // 편집 상태 (COMPLETED 상태에서만 활성)
    const firstPage = sortedPages[0];
    const [ocrText, setOcrText] = useState(firstPage?.ocr_text ?? '');
    const [literalText, setLiteralText] = useState(firstPage?.literal_text ?? '');
    const [interpretiveText, setInterpretiveText] = useState(firstPage?.interpretive_text ?? '');
    const [activeTab, setActiveTab] = useState<ActiveTab>('literal');
    const [saving, setSaving] = useState(false);
    const [saveError, setSaveError] = useState<string | null>(null);
    const [savedVersion, setSavedVersion] = useState<number | null>(null);

    const canEdit = book.status === 'COMPLETED' && !!firstPage;

    const handleRetry = async () => {
        setRetrying(true);
        setRetryError(null);
        try {
            await apiClient.post(API_ENDPOINTS.TRANSLATE_RETRY(book.book_id));
            navigate('/history');
        } catch (err) {
            if (err instanceof ApiError && err.code === 'NO_SOURCE_FILE') {
                setRetryError('이전 버전 번역이라 원본 파일이 없습니다. 새로 번역해주세요.');
            } else {
                setRetryError('재시도 요청에 실패했습니다. 잠시 후 다시 시도해주세요.');
            }
            setRetrying(false);
        }
    };

    const handleSave = async () => {
        if (!firstPage) return;
        setSaving(true);
        setSaveError(null);
        setSavedVersion(null);
        try {
            const res = await apiClient.put<{ version: number }>(
                API_ENDPOINTS.TRANSLATE_PAGE_EDIT(book.book_id, firstPage.page_no),
                {
                    ocr_text: ocrText || null,
                    literal_text: literalText,
                    interpretive_text: interpretiveText,
                },
            );
            setSavedVersion(res.version);
        } catch (err) {
            setSaveError(err instanceof ApiError ? err.message : '저장에 실패했습니다.');
        } finally {
            setSaving(false);
        }
    };

    return (
        <div className="page-wrapper py-8">
            <div className="container-main">
                {/* 뒤로가기 */}
                <Link
                    to="/history"
                    className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 mb-6 transition-colors"
                >
                    <ArrowLeft className="w-4 h-4" aria-hidden />
                    <span>번역 이력으로 돌아가기</span>
                </Link>

                {/* 책 정보 */}
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 px-6 py-5 mb-6">
                    <div className="flex items-center gap-3 flex-wrap">
                        {editingTitle ? (
                            <input
                                ref={titleInputRef}
                                value={title}
                                onChange={(e) => setTitle(e.target.value)}
                                onBlur={handleTitleSave}
                                onKeyDown={handleTitleKeyDown}
                                disabled={savingTitle}
                                className="text-[length:var(--text-page-title-mobile)] lg:text-[length:var(--text-page-title)] font-bold text-gray-900 border-b-2 border-blue-500 outline-none bg-transparent flex-1 min-w-0"
                                autoFocus
                            />
                        ) : (
                            <button
                                type="button"
                                onClick={handleTitleEdit}
                                className="group flex items-center gap-2 text-left min-w-0 overflow-hidden"
                            >
                                <h1 className="text-[length:var(--text-page-title-mobile)] lg:text-[length:var(--text-page-title)] font-bold text-gray-900 break-words min-w-0">
                                    {title}
                                </h1>
                                <Pencil className="w-4 h-4 text-gray-300 group-hover:text-gray-500 transition-colors shrink-0" aria-hidden />
                            </button>
                        )}
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

                {/* COMPLETED — 편집 가능 2열 레이아웃 */}
                {book.status === 'COMPLETED' && sortedPages.map((p) => (
                    <div key={p.page_no} className="mb-6">
                        {sortedPages.length > 1 && (
                            <p className="text-sm font-semibold text-gray-500 mb-2">{p.page_no}페이지</p>
                        )}
                        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
                            {/* 좌: 원문 */}
                            <div className="rounded-lg border border-gray-200 bg-white shadow-sm overflow-hidden">
                                <div className="flex items-center justify-between border-b border-gray-200 bg-gray-50 px-4 py-3">
                                    <span className="text-sm font-semibold text-gray-700">원문</span>
                                    {canEdit && p.page_no === firstPage!.page_no && (
                                        <button
                                            type="button"
                                            onClick={handleSave}
                                            disabled={saving}
                                            className="flex items-center gap-1.5 rounded-md bg-blue-600 px-3 py-1.5 text-sm font-medium text-white transition-colors hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                                        >
                                            {saving
                                                ? <><Loader2 className="w-3.5 h-3.5 animate-spin" aria-hidden />저장 중...</>
                                                : <><Save className="w-3.5 h-3.5" aria-hidden />저장</>
                                            }
                                        </button>
                                    )}
                                </div>
                                {canEdit && p.page_no === firstPage!.page_no ? (
                                    <textarea
                                        value={ocrText}
                                        onChange={(e) => setOcrText(e.target.value)}
                                        placeholder="원문을 입력하세요"
                                        className="w-full resize-none p-4 text-sm text-gray-800 placeholder:text-gray-400 focus:outline-none"
                                        rows={12}
                                    />
                                ) : (
                                    <div className="p-4">
                                        <pre className="text-sm text-gray-700 whitespace-pre-wrap font-sans break-words">
                                            {p.ocr_text || '—'}
                                        </pre>
                                    </div>
                                )}
                            </div>

                            {/* 우: 직역/의역 탭 */}
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
                                {canEdit && p.page_no === firstPage!.page_no ? (
                                    <textarea
                                        value={activeTab === 'literal' ? literalText : interpretiveText}
                                        onChange={(e) => activeTab === 'literal'
                                            ? setLiteralText(e.target.value)
                                            : setInterpretiveText(e.target.value)
                                        }
                                        placeholder={activeTab === 'literal' ? '직역 내용' : '의역 내용'}
                                        className="w-full resize-none p-4 text-sm text-gray-800 placeholder:text-gray-400 focus:outline-none"
                                        rows={12}
                                    />
                                ) : (
                                    <div className="p-4">
                                        <pre className="text-sm text-gray-700 whitespace-pre-wrap font-sans break-words">
                                            {(activeTab === 'literal' ? p.literal_text : p.interpretive_text) || '—'}
                                        </pre>
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* 저장 피드백 */}
                        {canEdit && p.page_no === firstPage!.page_no && (
                            <div className="mt-2 text-right text-sm">
                                {saveError && <span className="text-red-500">{saveError}</span>}
                                {savedVersion && <span className="text-green-600">저장 완료 (v{savedVersion})</span>}
                            </div>
                        )}
                    </div>
                ))}

                {/* 분석 결과 */}
                {book.status === 'COMPLETED' && (
                    <BookAnalyzeSection summaryText={book.summary_text} keywords={book.keywords} />
                )}

                {/* OCR 완료 대기 */}
                {book.status === 'OCR_COMPLETED' && (
                    <div className="rounded-lg border border-amber-200 bg-amber-50 px-6 py-5 mb-6">
                        <div className="flex items-center justify-between flex-wrap gap-3">
                            <div>
                                <p className="font-medium text-amber-800">OCR 인식이 완료되었습니다.</p>
                                <p className="mt-1 text-sm text-amber-700">원문을 확인하고 수정한 뒤 AI 번역을 실행하세요.</p>
                            </div>
                            <Link
                                to={`/translate?book_id=${book.book_id}`}
                                className="shrink-0 flex items-center gap-2 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors"
                            >
                                번역 이어하기 →
                            </Link>
                        </div>
                        {firstPage?.ocr_text && (
                            <div className="mt-4 rounded-md bg-amber-100 p-3">
                                <p className="text-xs font-semibold text-amber-600 uppercase mb-1">OCR 원문 미리보기</p>
                                <p className="text-sm text-amber-900 whitespace-pre-wrap line-clamp-4">{firstPage.ocr_text}</p>
                            </div>
                        )}
                    </div>
                )}

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
