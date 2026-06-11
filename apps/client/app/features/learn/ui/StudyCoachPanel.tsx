import { useState } from 'react';

import { Bot, Loader2, X } from 'lucide-react';

import { FlashcardBox } from './FlashcardBox';
import { TutorChat } from './TutorChat';

import type { LearnChatMessage } from '../types/chat';
import type { Flashcard, FlashcardReviewResult } from '../types/flashcard';
import type { StudyProgress } from '../types/progress';

interface Props {
    cards: Flashcard[];
    activeCard: Flashcard | null;
    tutorMessages: LearnChatMessage[];
    progress: StudyProgress;
    isGeneratingCards: boolean;
    isReviewing: boolean;
    isQuizzing: boolean;
    isTutorSending: boolean;
    coachError: string | null;
    onGenerateCards: () => void;
    onReview: (result: FlashcardReviewResult) => void;
    onQuiz: () => void;
    onSendTutor: (question: string) => void;
}

export function StudyCoachPanel({
    cards,
    activeCard,
    tutorMessages,
    progress,
    isGeneratingCards,
    isReviewing,
    isQuizzing,
    isTutorSending,
    coachError,
    onGenerateCards,
    onReview,
    onQuiz,
    onSendTutor,
}: Props) {
    const [isOpen, setIsOpen] = useState(false);

    const xpPercent = progress.level >= 99 ? 100 : Math.round((progress.level_xp / 120) * 100);

    return (
        <>
            <button
                type="button"
                onClick={() => setIsOpen((prev) => !prev)}
                aria-label={isOpen ? 'AI 학습 패널 닫기' : 'AI 학습 패널 열기'}
                className="fixed right-4 bottom-4 z-40 flex h-14 w-14 items-center justify-center rounded-full bg-gradient-to-br from-indigo-500 to-purple-500 text-white shadow-lg transition-transform hover:scale-105 lg:right-6 lg:bottom-6"
            >
                {isOpen ? <X className="h-6 w-6" aria-hidden /> : <Bot className="h-6 w-6" aria-hidden />}
            </button>

            {/* 모바일 오버레이 */}
            {isOpen && (
                <button
                    type="button"
                    aria-label="패널 닫기"
                    onClick={() => setIsOpen(false)}
                    className="fixed inset-0 z-40 bg-black/30 lg:hidden"
                />
            )}

            {isOpen && (
                <div className="fixed inset-x-0 bottom-0 z-50 flex max-h-[85vh] flex-col overflow-hidden rounded-t-2xl bg-white shadow-2xl lg:inset-x-auto lg:right-6 lg:bottom-24 lg:max-h-[82vh] lg:w-[420px] lg:rounded-2xl">
                    <div className="bg-gradient-to-br from-indigo-500 to-purple-500 p-5 text-white">
                        <div className="flex items-center justify-between gap-3">
                            <div>
                                <h2 className="text-lg font-bold">AI Study Coach</h2>
                                <p className="mt-1 text-xs opacity-90">문서 기반 학습 튜터</p>
                            </div>
                            <div className="flex items-center gap-2">
                                <span className="rounded-xl bg-white/20 px-3 py-1.5 text-sm font-bold">
                                    Lv.{progress.level}
                                </span>
                                <button
                                    type="button"
                                    onClick={() => setIsOpen(false)}
                                    aria-label="닫기"
                                    className="rounded-lg p-1 hover:bg-white/20 lg:hidden"
                                >
                                    <X className="h-5 w-5" aria-hidden />
                                </button>
                            </div>
                        </div>

                        <div className="mt-4 h-2 overflow-hidden rounded-full bg-white/20">
                            <div
                                className="h-full rounded-full bg-white transition-all"
                                style={{ width: `${xpPercent}%` }}
                            />
                        </div>
                        <p className="mt-1.5 text-xs opacity-85">
                            {progress.level >= 99 ? 'MAX LEVEL' : `${progress.level_xp} / 120 XP`}
                        </p>

                        <div className="mt-3 grid grid-cols-3 gap-2">
                            {[
                                { label: '연속 학습', value: `${progress.streak}일` },
                                { label: '복습 카드', value: `${cards.length}개` },
                                { label: '정답률', value: `${progress.accuracy}%` },
                            ].map(({ label, value }) => (
                                <div key={label} className="rounded-xl bg-white/15 px-3 py-2">
                                    <div className="text-xs opacity-80">{label}</div>
                                    <strong className="text-base">{value}</strong>
                                </div>
                            ))}
                        </div>
                    </div>

                    <div className="flex flex-1 flex-col gap-4 overflow-y-auto bg-gray-50 p-4">
                        <div className="rounded-2xl border border-gray-200 bg-white p-4">
                            <div className="mb-3 flex items-center justify-between">
                                <h3 className="text-sm font-semibold text-gray-800">오늘의 학습</h3>
                                <span className="text-xs font-bold text-indigo-600">DAILY</span>
                            </div>
                            <div className="flex flex-col gap-2.5">
                                <div className="flex items-center justify-between gap-3 rounded-xl bg-gray-50 p-3">
                                    <div>
                                        <strong className="text-sm text-gray-800">핵심 용어 카드 만들기</strong>
                                        <p className="mt-0.5 text-xs text-gray-500">
                                            문서에서 암기할 표현을 추출합니다.
                                        </p>
                                    </div>
                                    <button
                                        type="button"
                                        onClick={onGenerateCards}
                                        disabled={isGeneratingCards}
                                        className="flex shrink-0 items-center gap-1 rounded-lg bg-indigo-600 px-3 py-1.5 text-xs font-semibold text-white transition-colors hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50"
                                    >
                                        {isGeneratingCards && (
                                            <Loader2 className="h-3 w-3 animate-spin" aria-hidden />
                                        )}
                                        {cards.length > 0 ? '재생성' : '생성'}
                                    </button>
                                </div>
                                <div className="flex items-center justify-between gap-3 rounded-xl bg-gray-50 p-3">
                                    <div>
                                        <strong className="text-sm text-gray-800">문맥 퀴즈</strong>
                                        <p className="mt-0.5 text-xs text-gray-500">
                                            AI가 짧은 확인 질문을 만듭니다.
                                        </p>
                                    </div>
                                    <button
                                        type="button"
                                        onClick={onQuiz}
                                        disabled={isQuizzing}
                                        className="flex shrink-0 items-center gap-1 rounded-lg bg-indigo-600 px-3 py-1.5 text-xs font-semibold text-white transition-colors hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50"
                                    >
                                        {isQuizzing && <Loader2 className="h-3 w-3 animate-spin" aria-hidden />}
                                        시작
                                    </button>
                                </div>
                            </div>
                            {coachError && <p className="mt-3 text-xs text-red-500">{coachError}</p>}
                        </div>

                        <div className="rounded-2xl border border-gray-200 bg-white p-4">
                            <div className="mb-3 flex items-center justify-between">
                                <h3 className="text-sm font-semibold text-gray-800">AI 암기 카드</h3>
                                <span className="text-xs font-bold text-purple-600">FLASHCARD</span>
                            </div>
                            <FlashcardBox
                                activeCard={activeCard}
                                isReviewing={isReviewing}
                                onReview={onReview}
                            />
                        </div>

                        <div className="rounded-2xl border border-gray-200 bg-white p-4">
                            <div className="mb-3 flex items-center justify-between">
                                <h3 className="text-sm font-semibold text-gray-800">AI 튜터 대화</h3>
                                <span className="text-xs font-bold text-emerald-600">ONLINE</span>
                            </div>
                            <TutorChat
                                messages={tutorMessages}
                                isSending={isTutorSending}
                                onSend={onSendTutor}
                            />
                        </div>
                    </div>
                </div>
            )}
        </>
    );
}
