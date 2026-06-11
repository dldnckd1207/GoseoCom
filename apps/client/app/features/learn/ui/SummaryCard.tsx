import { Loader2, Sparkles } from 'lucide-react';

interface Props {
    summary: string | null;
    analysisItems: string[];
    isGenerating: boolean;
    error: string | null;
    onGenerate: () => void;
}

export function SummaryCard({ summary, analysisItems, isGenerating, error, onGenerate }: Props) {
    return (
        <div className="flex flex-col gap-4">
            <div className="rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-500 p-5 text-white shadow-sm">
                <div className="mb-3 flex items-center justify-between gap-3">
                    <h3 className="font-semibold">AI 요약</h3>
                    <button
                        type="button"
                        onClick={onGenerate}
                        disabled={isGenerating}
                        className="flex items-center gap-1.5 rounded-lg bg-white/20 px-3 py-1.5 text-xs font-semibold transition-colors hover:bg-white/30 disabled:cursor-not-allowed disabled:opacity-60"
                    >
                        {isGenerating ? (
                            <>
                                <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden />
                                생성 중...
                            </>
                        ) : (
                            <>
                                <Sparkles className="h-3.5 w-3.5" aria-hidden />
                                AI 요약
                            </>
                        )}
                    </button>
                </div>
                <p className="text-sm leading-relaxed opacity-95">
                    {summary ?? '문서 내용을 바탕으로 AI 요약을 생성할 수 있습니다.'}
                </p>
            </div>

            <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
                <div className="mb-3 flex items-center justify-between">
                    <h3 className="text-sm font-semibold text-gray-700">🧠 AI 학습 분석</h3>
                    <span className="text-xs font-bold text-indigo-600">AUTO</span>
                </div>
                {analysisItems.length === 0 ? (
                    <p className="text-sm text-gray-400">
                        AI 요약을 실행하면 최대 3개의 학습 포인트가 표시됩니다.
                    </p>
                ) : (
                    <ul className="flex flex-col gap-2">
                        {analysisItems.map((item) => (
                            <li
                                key={item}
                                className="rounded-xl bg-gray-50 px-3 py-2.5 text-sm leading-relaxed text-gray-800"
                            >
                                • {item}
                            </li>
                        ))}
                    </ul>
                )}
                {error && <p className="mt-3 text-sm text-red-500">{error}</p>}
            </div>
        </div>
    );
}
