from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.common.decorators.require_level import require_level
from app.core.common.enums import UserRole
from app.core.common.response import ApiResponse
from app.db.session import get_db
from app.learn.schemas import (
    ChatSendRequest,
    ChatSendResponse,
    FlashcardGenerateResponse,
    FlashcardReviewRequest,
    FlashcardReviewResponse,
    LearnWorkspaceResponse,
    QuizResponse,
    SummaryResponse,
)
from app.learn.service import LearnService

router = APIRouter(prefix="/api/v1/learn", tags=["learn"])


@router.get(
    "/books/{book_id}",
    summary="학습 워크스페이스 부트스트랩",
    response_model=ApiResponse[LearnWorkspaceResponse],
    status_code=status.HTTP_200_OK,
)
async def get_workspace(
    book_id: str,
    payload: dict[str, Any] = require_level(UserRole.USER),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[LearnWorkspaceResponse]:
    service = LearnService(db)
    data = await service.get_workspace(book_id, payload)
    return ApiResponse.success(data)


@router.post(
    "/books/{book_id}/chat",
    summary="문서 Q&A 챗봇 (동기)",
    response_model=ApiResponse[ChatSendResponse],
    status_code=status.HTTP_200_OK,
)
async def send_chat(
    book_id: str,
    req: ChatSendRequest,
    payload: dict[str, Any] = require_level(UserRole.USER),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[ChatSendResponse]:
    service = LearnService(db)
    data = await service.send_chat(book_id, req, payload)
    return ApiResponse.success(data)


@router.post(
    "/books/{book_id}/tutor",
    summary="AI 튜터 채팅 (동기, +10XP)",
    response_model=ApiResponse[ChatSendResponse],
    status_code=status.HTTP_200_OK,
)
async def send_tutor(
    book_id: str,
    req: ChatSendRequest,
    payload: dict[str, Any] = require_level(UserRole.USER),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[ChatSendResponse]:
    service = LearnService(db)
    data = await service.send_tutor(book_id, req, payload)
    return ApiResponse.success(data)


@router.post(
    "/books/{book_id}/summary",
    summary="AI 요약 + 학습 분석 (비영속)",
    response_model=ApiResponse[SummaryResponse],
    status_code=status.HTTP_200_OK,
)
async def generate_summary(
    book_id: str,
    payload: dict[str, Any] = require_level(UserRole.USER),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[SummaryResponse]:
    service = LearnService(db)
    data = await service.generate_summary(book_id, payload)
    return ApiResponse.success(data)


@router.post(
    "/books/{book_id}/flashcards",
    summary="AI 암기 카드 5개 생성 (기존 세트 교체, +20XP)",
    response_model=ApiResponse[FlashcardGenerateResponse],
    status_code=status.HTTP_201_CREATED,
)
async def generate_flashcards(
    book_id: str,
    payload: dict[str, Any] = require_level(UserRole.USER),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[FlashcardGenerateResponse]:
    service = LearnService(db)
    data = await service.generate_flashcards(book_id, payload)
    return ApiResponse.created(data, message="AI 암기 카드가 생성되었습니다.")


@router.post(
    "/books/{book_id}/flashcards/review",
    summary="암기 카드 복습 (KNOWN +8XP / NEXT +3XP, 회전)",
    response_model=ApiResponse[FlashcardReviewResponse],
    status_code=status.HTTP_200_OK,
)
async def review_flashcard(
    book_id: str,
    req: FlashcardReviewRequest,
    payload: dict[str, Any] = require_level(UserRole.USER),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[FlashcardReviewResponse]:
    service = LearnService(db)
    data = await service.review_flashcard(book_id, req, payload)
    return ApiResponse.success(data)


@router.post(
    "/books/{book_id}/quiz",
    summary="문맥 퀴즈 생성 → 튜터 메시지 (+15XP)",
    response_model=ApiResponse[QuizResponse],
    status_code=status.HTTP_200_OK,
)
async def generate_quiz(
    book_id: str,
    payload: dict[str, Any] = require_level(UserRole.USER),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[QuizResponse]:
    service = LearnService(db)
    data = await service.generate_quiz(book_id, payload)
    return ApiResponse.success(data)
