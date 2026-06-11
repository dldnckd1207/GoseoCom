import type { StudyProgress } from './progress';

type LearnChatMessage = {
    message_id: string;
    role: 'USER' | 'AI';
    content: string;
    created_at: string;
};

type ChatSendRequest = {
    question: string;
};

type ChatSendResponse = {
    user_message: LearnChatMessage;
    ai_message: LearnChatMessage;
    progress: StudyProgress | null;
};

type QuizResponse = {
    message: LearnChatMessage;
    progress: StudyProgress;
};

export type { LearnChatMessage, ChatSendRequest, ChatSendResponse, QuizResponse };
