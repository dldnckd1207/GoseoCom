import { useRef, useState } from 'react';

import { ApiError } from '~/shared/api/client';

import { sendChat } from '../api/chat.api';

import type { LearnChatMessage } from '../types/chat';

export function useLearnChat(bookId: string, initialMessages: LearnChatMessage[]) {
    const [messages, setMessages] = useState<LearnChatMessage[]>(initialMessages);
    const [isSending, setIsSending] = useState(false);
    const tempSeq = useRef(0);

    const send = async (question: string) => {
        const trimmed = question.trim();
        if (!trimmed || isSending) return;

        tempSeq.current += 1;
        const tempId = `temp-${tempSeq.current}`;
        setMessages((prev) => [
            ...prev,
            {
                message_id: tempId,
                role: 'USER',
                content: trimmed,
                created_at: new Date().toISOString(),
            },
        ]);
        setIsSending(true);
        try {
            const res = await sendChat(bookId, trimmed);
            setMessages((prev) => [
                ...prev.filter((m) => m.message_id !== tempId),
                res.user_message,
                res.ai_message,
            ]);
        } catch (err) {
            const message = err instanceof ApiError ? err.message : '답변 생성에 실패했습니다.';
            tempSeq.current += 1;
            setMessages((prev) => [
                ...prev,
                {
                    message_id: `temp-${tempSeq.current}`,
                    role: 'AI',
                    content: message,
                    created_at: new Date().toISOString(),
                },
            ]);
        } finally {
            setIsSending(false);
        }
    };

    return { messages, isSending, send };
}
