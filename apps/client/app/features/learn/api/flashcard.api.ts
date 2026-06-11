import { apiClient } from '~/shared/api/client';
import { API_ENDPOINTS } from '~/shared/api/endpoints';

import type {
    FlashcardGenerateResponse,
    FlashcardReviewResponse,
    FlashcardReviewResult,
} from '../types/flashcard';

export async function generateFlashcards(bookId: string): Promise<FlashcardGenerateResponse> {
    return apiClient.post<FlashcardGenerateResponse>(API_ENDPOINTS.LEARN_FLASHCARDS(bookId));
}

export async function reviewFlashcard(
    bookId: string,
    result: FlashcardReviewResult,
): Promise<FlashcardReviewResponse> {
    return apiClient.post<FlashcardReviewResponse>(API_ENDPOINTS.LEARN_FLASHCARD_REVIEW(bookId), {
        result,
    });
}
