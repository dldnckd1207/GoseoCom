import { apiClient } from '~/shared/api/client';
import { API_ENDPOINTS } from '~/shared/api/endpoints';

import type { ChatSendResponse } from '../types/chat';

export async function sendChat(bookId: string, question: string): Promise<ChatSendResponse> {
    return apiClient.post<ChatSendResponse>(API_ENDPOINTS.LEARN_CHAT(bookId), { question });
}

export async function sendTutor(bookId: string, question: string): Promise<ChatSendResponse> {
    return apiClient.post<ChatSendResponse>(API_ENDPOINTS.LEARN_TUTOR(bookId), { question });
}
