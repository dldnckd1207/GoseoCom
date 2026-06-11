import { apiClient } from '~/shared/api/client';
import { API_ENDPOINTS } from '~/shared/api/endpoints';

import type { QuizResponse } from '../types/chat';
import type { SummaryResponse } from '../types/progress';

export async function generateSummary(bookId: string): Promise<SummaryResponse> {
    return apiClient.post<SummaryResponse>(API_ENDPOINTS.LEARN_SUMMARY(bookId));
}

export async function generateQuiz(bookId: string): Promise<QuizResponse> {
    return apiClient.post<QuizResponse>(API_ENDPOINTS.LEARN_QUIZ(bookId));
}
