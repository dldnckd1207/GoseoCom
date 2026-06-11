import type { Flashcard } from '../types/flashcard';
import type { FlashcardReviewResult } from '../types/flashcard';

interface Props {
    activeCard: Flashcard | null;
    isReviewing: boolean;
    onReview: (result: FlashcardReviewResult) => void;
}

export function FlashcardBox({ activeCard, isReviewing, onReview }: Props) {
    return (
        <div className="rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-500 p-5 text-white">
            <div className="text-xs opacity-85">{activeCard?.card_type ?? '단어 카드'}</div>
            <h2 className="mt-2 text-2xl font-bold">{activeCard?.term ?? '준비됨'}</h2>
            <p className="mt-3 text-sm leading-relaxed opacity-95">
                {activeCard?.meaning ?? '카드를 생성하거나 복습을 시작하세요.'}
            </p>
            <div className="mt-4 flex gap-2">
                <button
                    type="button"
                    onClick={() => onReview('KNOWN')}
                    disabled={!activeCard || isReviewing}
                    className="flex-1 rounded-xl bg-white px-3 py-2.5 text-sm font-bold text-indigo-600 transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
                >
                    암기 완료
                </button>
                <button
                    type="button"
                    onClick={() => onReview('NEXT')}
                    disabled={!activeCard || isReviewing}
                    className="flex-1 rounded-xl bg-white/20 px-3 py-2.5 text-sm font-bold text-white transition-colors hover:bg-white/30 disabled:cursor-not-allowed disabled:opacity-50"
                >
                    다음 카드
                </button>
            </div>
        </div>
    );
}
