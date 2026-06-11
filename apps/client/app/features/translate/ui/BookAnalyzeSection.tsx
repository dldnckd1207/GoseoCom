import type { KeywordItem } from '~/shared/types/translate';

type Props = {
    summaryText: string | null;
    keywords: KeywordItem[] | null;
};

export function BookAnalyzeSection({ summaryText, keywords }: Props) {
    if (!summaryText && (!keywords || keywords.length === 0)) return null;

    const sorted = [...(keywords ?? [])].sort((a, b) => b.count - a.count);

    return (
        <div className="space-y-4 mt-6">
            {summaryText && (
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                    <p className="text-xs font-semibold text-gray-400 uppercase mb-3">핵심 요약</p>
                    <p className="text-sm text-gray-700 leading-relaxed">{summaryText}</p>
                </div>
            )}
            {sorted.length > 0 && (
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                    <p className="text-xs font-semibold text-gray-400 uppercase mb-3">주요 한자어</p>
                    <ul className="flex flex-wrap gap-2">
                        {sorted.map((kw) => (
                            <li
                                key={kw.word}
                                title={kw.meaning}
                                className="flex items-center gap-1 rounded-full border border-gray-200 bg-gray-50 px-3 py-1 text-sm cursor-default hover:bg-blue-50 hover:border-blue-200 transition-colors"
                            >
                                <span className="font-medium text-gray-800">{kw.word}</span>
                                <span className="text-gray-400">({kw.reading})</span>
                                <span className="text-xs text-gray-400">×{kw.count}</span>
                            </li>
                        ))}
                    </ul>
                </div>
            )}
        </div>
    );
}
