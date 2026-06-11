import type { StudyProgress } from './progress';

type Flashcard = {
    card_id: string;
    term: string;
    meaning: string;
    card_type: string;
    known_yn: boolean;
};

type FlashcardReviewResult = 'KNOWN' | 'NEXT';

type FlashcardGenerateResponse = {
    cards: Flashcard[];
    progress: StudyProgress;
};

type FlashcardReviewResponse = {
    active_card: Flashcard | null;
    progress: StudyProgress;
};

export type { Flashcard, FlashcardReviewResult, FlashcardGenerateResponse, FlashcardReviewResponse };
