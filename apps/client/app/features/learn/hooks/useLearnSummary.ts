import { useState } from 'react';

import { ApiError } from '~/shared/api/client';

import { generateSummary } from '../api/study.api';

export function useLearnSummary(bookId: string, initialSummary: string | null) {
    const [summary, setSummary] = useState<string | null>(initialSummary);
    const [analysisItems, setAnalysisItems] = useState<string[]>([]);
    const [isGenerating, setIsGenerating] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const generate = async () => {
        if (isGenerating) return;
        setIsGenerating(true);
        setError(null);
        try {
            const res = await generateSummary(bookId);
            setSummary(res.summary);
            setAnalysisItems(res.analysis_items);
        } catch (err) {
            setError(err instanceof ApiError ? err.message : 'AI 요약 생성에 실패했습니다.');
        } finally {
            setIsGenerating(false);
        }
    };

    return { summary, analysisItems, isGenerating, error, generate };
}
