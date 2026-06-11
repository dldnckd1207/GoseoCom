import { useLoaderData } from 'react-router';

import {
    BookSelector,
    LearnChat,
    OriginalPanel,
    StudyCoachPanel,
    SummaryCard,
    TranslationPanel,
    useLearnChat,
    useLearnSummary,
    useStudyCoach,
} from '~/features/learn';

import type { LearnWorkspaceResponse } from '~/features/learn';
import type { loader } from '~/routes/_protected.translate-test';

export function TranslateTestView() {
    const data = useLoaderData<typeof loader>();

    if (data.mode === 'select') {
        return (
            <div className="page-wrapper py-8">
                <div className="container-main">
                    <BookSelector books={data.books} error={data.error} />
                </div>
            </div>
        );
    }

    return <WorkspaceView workspace={data.workspace} />;
}

function WorkspaceView({ workspace }: { workspace: LearnWorkspaceResponse }) {
    const chat = useLearnChat(workspace.book_id, workspace.chat_messages);
    const summary = useLearnSummary(workspace.book_id, workspace.summary_text);
    const coach = useStudyCoach(workspace.book_id, {
        flashcards: workspace.flashcards,
        tutorMessages: workspace.tutor_messages,
        progress: workspace.progress,
    });

    return (
        <div className="page-wrapper py-8">
            <div className="container-main">
                <div className="mb-6">
                    <h1 className="mb-2 text-[length:var(--text-page-title-mobile)] font-bold text-gray-900 lg:text-[length:var(--text-page-title)]">
                        {workspace.title}
                    </h1>
                    <p className="text-gray-600">AI 문서 해석 · 학습 보조 워크스페이스 (Beta)</p>
                </div>

                {/* 원본 이미지+OCR | 직역·의역 토글+채팅 | AI 요약+학습 분석 */}
                <div className="grid grid-cols-1 gap-5 lg:grid-cols-[1fr_1.1fr_0.9fr]">
                    <OriginalPanel
                        sourceFileUrl={workspace.source_file_url}
                        pages={workspace.pages}
                    />
                    <div className="flex flex-col gap-5">
                        <TranslationPanel pages={workspace.pages} />
                        <LearnChat
                            messages={chat.messages}
                            isSending={chat.isSending}
                            onSend={chat.send}
                        />
                    </div>
                    <SummaryCard
                        summary={summary.summary}
                        analysisItems={summary.analysisItems}
                        isGenerating={summary.isGenerating}
                        error={summary.error}
                        onGenerate={summary.generate}
                    />
                </div>
            </div>

            <StudyCoachPanel
                cards={coach.cards}
                activeCard={coach.activeCard}
                tutorMessages={coach.tutorMessages}
                progress={coach.progress}
                isGeneratingCards={coach.isGeneratingCards}
                isReviewing={coach.isReviewing}
                isQuizzing={coach.isQuizzing}
                isTutorSending={coach.isTutorSending}
                coachError={coach.coachError}
                onGenerateCards={coach.generateCards}
                onReview={coach.review}
                onQuiz={coach.quiz}
                onSendTutor={coach.sendTutorMessage}
            />
        </div>
    );
}
