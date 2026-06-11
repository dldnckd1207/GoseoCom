from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.learn.models import LearnStudyProgress

XP_CAP = 11760  # Lv.99 도달 XP 상한 (프로토타입 시맨틱)
XP_PER_LEVEL = 120


class LearnPageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    page_no: int = Field(..., description="페이지 번호", examples=[1])
    ocr_text: str | None = Field(None, description="OCR 원문")
    literal_text: str | None = Field(None, description="직역")
    interpretive_text: str | None = Field(None, description="의역")


class ChatMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    message_id: str = Field(
        ..., validation_alias="id", description="메시지 ID", examples=["LMSG_00000001"]
    )
    role: str = Field(..., description="작성 주체 (USER | AI)", examples=["AI"])
    content: str = Field(..., description="메시지 내용")
    created_at: datetime = Field(..., description="작성 일시")


class StudyProgressResponse(BaseModel):
    xp: int = Field(..., description="누적 XP", examples=[120])
    level: int = Field(..., description="레벨 (120 XP당 1, 최대 99)", examples=[2])
    level_xp: int = Field(..., description="현재 레벨 내 XP", examples=[0])
    streak: int = Field(..., description="연속 학습 일수", examples=[3])
    reviewed_cnt: int = Field(..., description="학습 활동 횟수", examples=[10])
    correct_cnt: int = Field(..., description="정답(암기 완료) 횟수", examples=[8])
    accuracy: int = Field(..., description="정답률(%)", examples=[80])

    @classmethod
    def from_model(cls, progress: LearnStudyProgress | None) -> "StudyProgressResponse":
        if progress is None:
            return cls(
                xp=0, level=1, level_xp=0, streak=0, reviewed_cnt=0, correct_cnt=0, accuracy=0
            )
        level = min(99, progress.xp // XP_PER_LEVEL + 1)
        accuracy = (
            round(progress.correct_cnt / progress.reviewed_cnt * 100)
            if progress.reviewed_cnt
            else 0
        )
        return cls(
            xp=progress.xp,
            level=level,
            level_xp=progress.xp % XP_PER_LEVEL,
            streak=progress.streak,
            reviewed_cnt=progress.reviewed_cnt,
            correct_cnt=progress.correct_cnt,
            accuracy=accuracy,
        )


class FlashcardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    card_id: str = Field(
        ..., validation_alias="id", description="카드 ID", examples=["LCARD_00000001"]
    )
    term: str = Field(..., description="용어", examples=["真身"])
    meaning: str = Field(..., description="뜻/문맥")
    card_type: str = Field(..., description="카드 유형", examples=["단어 카드"])
    known_yn: bool = Field(..., description="암기 완료 여부", examples=[False])


class LearnWorkspaceResponse(BaseModel):
    book_id: str = Field(..., description="Book ID", examples=["BOOK_00000001"])
    title: str = Field(..., description="문서 제목")
    source_file_url: str | None = Field(None, description="원문 이미지 URL")
    summary_text: str | None = Field(None, description="분석 파이프라인 요약 (초기 표시용)")
    keywords: list[dict[str, object]] | None = Field(
        None, description="분석 키워드 (한자어+뜻+빈도)"
    )
    pages: list[LearnPageResponse] = Field(..., description="페이지별 번역 결과")
    chat_messages: list[ChatMessageResponse] = Field(..., description="문서 Q&A 대화 기록")
    tutor_messages: list[ChatMessageResponse] = Field(..., description="AI 튜터 대화 기록")
    flashcards: list[FlashcardResponse] = Field(..., description="암기 카드 (sort_order 순)")
    progress: StudyProgressResponse = Field(..., description="학습 진행도")


class ChatSendRequest(BaseModel):
    question: str = Field(
        ..., min_length=1, max_length=1000, description="사용자 질문", examples=["真身의 의미는?"]
    )


class ChatSendResponse(BaseModel):
    user_message: ChatMessageResponse = Field(..., description="저장된 사용자 메시지")
    ai_message: ChatMessageResponse = Field(..., description="AI 응답 메시지")
    progress: StudyProgressResponse | None = Field(
        None, description="갱신된 진행도 (XP 변동 없으면 null)"
    )


class SummaryResponse(BaseModel):
    summary: str = Field(..., description="AI 요약 (2~3문장)")
    analysis_items: list[str] = Field(..., description="학습 분석 bullet (최대 3개)")


class FlashcardGenerateResponse(BaseModel):
    cards: list[FlashcardResponse] = Field(..., description="생성된 카드 (5개)")
    progress: StudyProgressResponse = Field(..., description="갱신된 진행도")


class FlashcardReviewRequest(BaseModel):
    result: Literal["KNOWN", "NEXT"] = Field(
        ..., description="복습 결과 — KNOWN(암기 완료) | NEXT(다음 카드)"
    )


class FlashcardReviewResponse(BaseModel):
    active_card: FlashcardResponse | None = Field(None, description="회전 후 현재 카드")
    progress: StudyProgressResponse = Field(..., description="갱신된 진행도")


class QuizResponse(BaseModel):
    message: ChatMessageResponse = Field(..., description="튜터 세션에 추가된 퀴즈 메시지")
    progress: StudyProgressResponse = Field(..., description="갱신된 진행도")
