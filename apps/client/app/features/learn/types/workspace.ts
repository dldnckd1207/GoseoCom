import type { LearnChatMessage } from './chat';
import type { Flashcard } from './flashcard';
import type { StudyProgress } from './progress';

type LearnPage = {
    page_no: number;
    ocr_text: string | null;
    literal_text: string | null;
    interpretive_text: string | null;
};

type BookKeyword = {
    word: string;
    reading?: string;
    meaning?: string;
    count?: number;
};

type LearnWorkspaceResponse = {
    book_id: string;
    title: string;
    source_file_url: string | null;
    summary_text: string | null;
    keywords: BookKeyword[] | null;
    pages: LearnPage[];
    chat_messages: LearnChatMessage[];
    tutor_messages: LearnChatMessage[];
    flashcards: Flashcard[];
    progress: StudyProgress;
};

// 책 선택 드롭다운 항목 — GET /api/v1/translate/mine 응답 (features/translate import 금지, 로컬 정의)
type BookDropdownItem = {
    book_id: string;
    title: string;
    source_file_url: string | null;
    created_at: string;
};

export type { LearnPage, BookKeyword, LearnWorkspaceResponse, BookDropdownItem };
