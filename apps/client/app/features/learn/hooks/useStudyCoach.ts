import { useRef, useState } from 'react';

import { ApiError } from '~/shared/api/client';

import { sendTutor } from '../api/chat.api';
import { generateFlashcards, reviewFlashcard } from '../api/flashcard.api';
import { generateQuiz } from '../api/study.api';

import type { LearnChatMessage } from '../types/chat';
import type { Flashcard, FlashcardReviewResult } from '../types/flashcard';
import type { StudyProgress } from '../types/progress';

type StudyCoachInit = {
    flashcards: Flashcard[];
    tutorMessages: LearnChatMessage[];
    progress: StudyProgress;
};

export function useStudyCoach(bookId: string, init: StudyCoachInit) {
    const [cards, setCards] = useState<Flashcard[]>(init.flashcards);
    const [tutorMessages, setTutorMessages] = useState<LearnChatMessage[]>(init.tutorMessages);
    const [progress, setProgress] = useState<StudyProgress>(init.progress);
    const [isGeneratingCards, setIsGeneratingCards] = useState(false);
    const [isReviewing, setIsReviewing] = useState(false);
    const [isQuizzing, setIsQuizzing] = useState(false);
    const [isTutorSending, setIsTutorSending] = useState(false);
    const [coachError, setCoachError] = useState<string | null>(null);
    const tempSeq = useRef(0);

    const activeCard = cards[0] ?? null;

    const appendTutorMessage = (role: 'USER' | 'AI', content: string) => {
        tempSeq.current += 1;
        setTutorMessages((prev) => [
            ...prev,
            {
                message_id: `temp-${tempSeq.current}`,
                role,
                content,
                created_at: new Date().toISOString(),
            },
        ]);
    };

    const generateCards = async () => {
        if (isGeneratingCards) return;
        setIsGeneratingCards(true);
        setCoachError(null);
        try {
            const res = await generateFlashcards(bookId);
            setCards(res.cards);
            setProgress(res.progress);
        } catch (err) {
            setCoachError(err instanceof ApiError ? err.message : '카드 생성에 실패했습니다.');
        } finally {
            setIsGeneratingCards(false);
        }
    };

    const review = async (result: FlashcardReviewResult) => {
        if (isReviewing || !activeCard) return;
        setIsReviewing(true);
        setCoachError(null);
        try {
            const res = await reviewFlashcard(bookId, result);
            setProgress(res.progress);
            // 첫 카드를 맨 뒤로 회전 (서버 sort_order와 동일한 시맨틱)
            setCards((prev) => {
                if (prev.length <= 1) {
                    return res.active_card ? [res.active_card] : prev;
                }
                const [first, ...rest] = prev;
                const reviewed = result === 'KNOWN' ? { ...first, known_yn: true } : first;
                return [...rest, reviewed];
            });
        } catch (err) {
            setCoachError(err instanceof ApiError ? err.message : '카드 복습에 실패했습니다.');
        } finally {
            setIsReviewing(false);
        }
    };

    const quiz = async () => {
        if (isQuizzing) return;
        setIsQuizzing(true);
        setCoachError(null);
        try {
            const res = await generateQuiz(bookId);
            setTutorMessages((prev) => [...prev, res.message]);
            setProgress(res.progress);
        } catch (err) {
            setCoachError(err instanceof ApiError ? err.message : '퀴즈 생성에 실패했습니다.');
        } finally {
            setIsQuizzing(false);
        }
    };

    const sendTutorMessage = async (question: string) => {
        const trimmed = question.trim();
        if (!trimmed || isTutorSending) return;
        appendTutorMessage('USER', trimmed);
        setIsTutorSending(true);
        setCoachError(null);
        try {
            const res = await sendTutor(bookId, trimmed);
            setTutorMessages((prev) => [...prev.slice(0, -1), res.user_message, res.ai_message]);
            if (res.progress) setProgress(res.progress);
        } catch (err) {
            appendTutorMessage(
                'AI',
                err instanceof ApiError ? err.message : '답변 생성에 실패했습니다.',
            );
        } finally {
            setIsTutorSending(false);
        }
    };

    return {
        cards,
        activeCard,
        tutorMessages,
        progress,
        isGeneratingCards,
        isReviewing,
        isQuizzing,
        isTutorSending,
        coachError,
        generateCards,
        review,
        quiz,
        sendTutorMessage,
    };
}
