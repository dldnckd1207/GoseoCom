import json
import logging
from datetime import UTC, datetime
from typing import Any
from zoneinfo import ZoneInfo

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.common.id_generator import next_id
from app.learn import prompts
from app.learn.models import LearnChatMessage, LearnChatSession, LearnFlashcard, LearnStudyProgress
from app.learn.repository import LearnRepository
from app.learn.schemas import (
    XP_CAP,
    ChatMessageResponse,
    ChatSendRequest,
    ChatSendResponse,
    FlashcardGenerateResponse,
    FlashcardResponse,
    FlashcardReviewRequest,
    FlashcardReviewResponse,
    LearnPageResponse,
    LearnWorkspaceResponse,
    QuizResponse,
    StudyProgressResponse,
    SummaryResponse,
)
from app.translate.models import Book

logger = logging.getLogger(__name__)

SESSION_DOC_QA = "DOC_QA"
SESSION_TUTOR = "TUTOR"

XP_TUTOR = 10
XP_QUIZ = 15
XP_FLASHCARDS = 20
XP_REVIEW_KNOWN = 8
XP_REVIEW_NEXT = 3

FLASHCARD_COUNT = 5

# 학습일(streak) 경계는 한국 시간 기준 — UTC date()를 쓰면 KST 00~09시 학습이 전날로 집계됨
KST = ZoneInfo("Asia/Seoul")


class LearnService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = LearnRepository(db)

    # ── 공통 헬퍼 ────────────────────────────────────────────────────

    async def _get_owned_completed_book(self, book_id: str, user_id: str) -> Book:
        book = await self.repo.get_book_with_pages(book_id)
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "BOOK_NOT_FOUND", "message": "번역 결과를 찾을 수 없습니다."},
            )
        if book.owner_user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "FORBIDDEN", "message": "접근 권한이 없습니다."},
            )
        if book.status != "COMPLETED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "BOOK_NOT_COMPLETED",
                    "message": "번역이 완료된 문서만 학습할 수 있습니다.",
                },
            )
        return book

    async def _get_or_create_session(
        self, user_id: str, book_id: str, session_type: str
    ) -> LearnChatSession:
        session = await self.repo.get_session(user_id, book_id, session_type)
        if session:
            return session
        now = datetime.now(UTC)
        session = LearnChatSession(
            id=await next_id("LSES_", self.db),
            user_id=user_id,
            book_id=book_id,
            session_type=session_type,
            created_at=now,
            created_by=user_id,
            updated_at=now,
            updated_by=user_id,
        )
        return await self.repo.create_session(session)

    async def _add_message(
        self, session_id: str, user_id: str, role: str, content: str
    ) -> LearnChatMessage:
        now = datetime.now(UTC)
        message = LearnChatMessage(
            id=await next_id("LMSG_", self.db),
            session_id=session_id,
            role=role,
            content=content,
            created_at=now,
            created_by=user_id,
            updated_at=now,
            updated_by=user_id,
        )
        return await self.repo.add_message(message)

    async def _add_xp(self, user_id: str, amount: int, is_correct: bool) -> LearnStudyProgress:
        """XP 적립 — 진행도 행이 없으면 생성. 프로토타입 시맨틱 유지(상한/연속학습/통계)."""
        progress = await self.repo.get_progress(user_id)
        now = datetime.now(UTC)
        if progress is None:
            progress = LearnStudyProgress(
                id=await next_id("LPRG_", self.db),
                user_id=user_id,
                created_at=now,
                created_by=user_id,
                updated_at=now,
                updated_by=user_id,
            )
            progress = await self.repo.create_progress(progress)
        today = now.astimezone(KST).date()
        if progress.last_study_date != today:
            progress.streak += 1
            progress.last_study_date = today
        progress.xp = min(XP_CAP, progress.xp + amount)
        progress.reviewed_cnt += 1
        if is_correct:
            progress.correct_cnt += 1
        progress.updated_at = now
        progress.updated_by = user_id
        await self.db.flush()
        return progress

    async def _generate_ai(
        self, prompt: str, *, json_mode: bool = False, temperature: float | None = None
    ) -> str:
        try:
            return await prompts.generate(prompt, json_mode=json_mode, temperature=temperature)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"code": "AI_UNAVAILABLE", "message": "AI 설정이 올바르지 않습니다."},
            ) from e
        except TimeoutError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"code": "AI_TIMEOUT", "message": "AI 응답이 지연되고 있습니다."},
            ) from e
        except HTTPException:
            raise
        except Exception as e:
            logger.error("[learn] Gemini 호출 실패: %s", e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"code": "AI_UNAVAILABLE", "message": "AI 호출에 실패했습니다."},
            ) from e

    @staticmethod
    def _history(messages: list[LearnChatMessage]) -> list[tuple[str, str]]:
        return [(m.role, m.content) for m in messages]

    # ── 워크스페이스 ─────────────────────────────────────────────────

    async def get_workspace(self, book_id: str, payload: dict[str, Any]) -> LearnWorkspaceResponse:
        user_id: str = payload["sub"]
        book = await self._get_owned_completed_book(book_id, user_id)

        chat_messages: list[LearnChatMessage] = []
        tutor_messages: list[LearnChatMessage] = []
        sessions = {s.session_type: s for s in await self.repo.list_sessions(user_id, book_id)}
        if SESSION_DOC_QA in sessions:
            chat_messages = await self.repo.list_messages(sessions[SESSION_DOC_QA].id)
        if SESSION_TUTOR in sessions:
            tutor_messages = await self.repo.list_messages(sessions[SESSION_TUTOR].id)

        flashcards = await self.repo.list_flashcards(user_id, book_id)
        progress = await self.repo.get_progress(user_id)

        pages = sorted((p for p in book.pages if not p.del_yn), key=lambda p: p.page_no)
        return LearnWorkspaceResponse(
            book_id=book.id,
            title=book.title,
            source_file_url=book.source_file.url_path if book.source_file else None,
            summary_text=book.summary_text,
            keywords=book.keywords,
            pages=[LearnPageResponse.model_validate(p) for p in pages],
            chat_messages=[ChatMessageResponse.model_validate(m) for m in chat_messages],
            tutor_messages=[ChatMessageResponse.model_validate(m) for m in tutor_messages],
            flashcards=[FlashcardResponse.model_validate(c) for c in flashcards],
            progress=StudyProgressResponse.from_model(progress),
        )

    # ── 채팅 (문서 Q&A / 튜터) ───────────────────────────────────────

    async def send_chat(
        self, book_id: str, req: ChatSendRequest, payload: dict[str, Any]
    ) -> ChatSendResponse:
        return await self._send_message(book_id, req, payload, SESSION_DOC_QA)

    async def send_tutor(
        self, book_id: str, req: ChatSendRequest, payload: dict[str, Any]
    ) -> ChatSendResponse:
        return await self._send_message(book_id, req, payload, SESSION_TUTOR)

    async def _send_message(
        self, book_id: str, req: ChatSendRequest, payload: dict[str, Any], session_type: str
    ) -> ChatSendResponse:
        user_id: str = payload["sub"]
        book = await self._get_owned_completed_book(book_id, user_id)
        session = await self._get_or_create_session(user_id, book_id, session_type)
        history = self._history(await self.repo.list_messages(session.id))

        doc_context = prompts.build_doc_context([p for p in book.pages if not p.del_yn])
        if session_type == SESSION_TUTOR:
            prompt = prompts.build_tutor_prompt(doc_context, history, req.question)
        else:
            prompt = prompts.build_chat_prompt(doc_context, history, req.question)

        answer = await self._generate_ai(prompt)
        if not answer:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"code": "AI_RESPONSE_INVALID", "message": "응답을 생성하지 못했습니다."},
            )

        user_message = await self._add_message(session.id, user_id, "USER", req.question)
        ai_message = await self._add_message(session.id, user_id, "AI", answer)

        progress: LearnStudyProgress | None = None
        if session_type == SESSION_TUTOR:
            progress = await self._add_xp(user_id, XP_TUTOR, is_correct=True)

        await self.db.commit()
        return ChatSendResponse(
            user_message=ChatMessageResponse.model_validate(user_message),
            ai_message=ChatMessageResponse.model_validate(ai_message),
            progress=StudyProgressResponse.from_model(progress) if progress else None,
        )

    # ── AI 요약 + 학습 분석 (비영속) ─────────────────────────────────

    async def generate_summary(self, book_id: str, payload: dict[str, Any]) -> SummaryResponse:
        user_id: str = payload["sub"]
        book = await self._get_owned_completed_book(book_id, user_id)
        doc_context = prompts.build_doc_context([p for p in book.pages if not p.del_yn])

        raw = await self._generate_ai(prompts.build_summary_prompt(doc_context), json_mode=True)
        try:
            parsed = prompts.parse_json_object(raw)
        except (json.JSONDecodeError, ValueError) as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"code": "AI_RESPONSE_INVALID", "message": "AI 응답 해석에 실패했습니다."},
            ) from e

        summary = str(parsed.get("summary", "")).strip()
        raw_items = parsed.get("analysis", [])
        items = (
            [str(item).strip() for item in raw_items if str(item).strip()]
            if isinstance(raw_items, list)
            else []
        )
        if not summary:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"code": "AI_RESPONSE_INVALID", "message": "요약을 생성하지 못했습니다."},
            )
        return SummaryResponse(summary=summary, analysis_items=items[:3])

    # ── 암기 카드 ────────────────────────────────────────────────────

    async def generate_flashcards(
        self, book_id: str, payload: dict[str, Any]
    ) -> FlashcardGenerateResponse:
        user_id: str = payload["sub"]
        book = await self._get_owned_completed_book(book_id, user_id)
        doc_context = prompts.build_doc_context([p for p in book.pages if not p.del_yn])

        keyword_hints: list[str] | None = None
        if book.keywords:
            keyword_hints = [
                f"{kw.get('word', '')}({kw.get('reading', '')}): {kw.get('meaning', '')}"
                for kw in book.keywords
                if kw.get("word")
            ]

        raw = await self._generate_ai(
            prompts.build_flashcards_prompt(doc_context, keyword_hints), json_mode=True
        )
        try:
            parsed = prompts.parse_json_array(raw)
        except (json.JSONDecodeError, ValueError) as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"code": "AI_RESPONSE_INVALID", "message": "AI 응답 해석에 실패했습니다."},
            ) from e

        normalized: list[tuple[str, str, str]] = []
        for item in parsed:
            if not isinstance(item, dict):
                continue
            term = str(item.get("term", "")).strip()
            meaning = str(item.get("meaning", "")).strip()
            card_type = str(item.get("type", "단어 카드")).strip() or "단어 카드"
            if term and meaning:
                normalized.append((term[:200], meaning, card_type[:30]))
        normalized = normalized[:FLASHCARD_COUNT]
        if not normalized:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"code": "AI_RESPONSE_INVALID", "message": "카드를 생성하지 못했습니다."},
            )

        await self.repo.soft_delete_flashcards(user_id, book_id, user_id)
        now = datetime.now(UTC)
        cards: list[LearnFlashcard] = []
        for order, (term, meaning, card_type) in enumerate(normalized):
            card = LearnFlashcard(
                id=await next_id("LCARD_", self.db),
                user_id=user_id,
                book_id=book_id,
                term=term,
                meaning=meaning,
                card_type=card_type,
                sort_order=order,
                created_at=now,
                created_by=user_id,
                updated_at=now,
                updated_by=user_id,
            )
            cards.append(await self.repo.add_flashcard(card))

        progress = await self._add_xp(user_id, XP_FLASHCARDS, is_correct=True)
        await self.db.commit()
        return FlashcardGenerateResponse(
            cards=[FlashcardResponse.model_validate(c) for c in cards],
            progress=StudyProgressResponse.from_model(progress),
        )

    async def review_flashcard(
        self, book_id: str, req: FlashcardReviewRequest, payload: dict[str, Any]
    ) -> FlashcardReviewResponse:
        user_id: str = payload["sub"]
        await self._get_owned_completed_book(book_id, user_id)

        cards = await self.repo.list_flashcards(user_id, book_id)
        if not cards:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "FLASHCARD_NOT_FOUND",
                    "message": "먼저 AI 암기 카드를 생성해 주세요.",
                },
            )

        now = datetime.now(UTC)
        current = cards[0]
        if req.result == "KNOWN":
            current.known_yn = True
        current.updated_at = now
        current.updated_by = user_id

        if len(cards) > 1:
            # 첫 카드를 맨 뒤로 회전 (sort_order 재배열)
            rotated = [*cards[1:], current]
            for order, card in enumerate(rotated):
                card.sort_order = order
            cards = rotated
        await self.db.flush()

        is_known = req.result == "KNOWN"
        progress = await self._add_xp(
            user_id, XP_REVIEW_KNOWN if is_known else XP_REVIEW_NEXT, is_correct=is_known
        )
        await self.db.commit()
        return FlashcardReviewResponse(
            active_card=FlashcardResponse.model_validate(cards[0]),
            progress=StudyProgressResponse.from_model(progress),
        )

    # ── 문맥 퀴즈 ────────────────────────────────────────────────────

    async def generate_quiz(self, book_id: str, payload: dict[str, Any]) -> QuizResponse:
        user_id: str = payload["sub"]
        book = await self._get_owned_completed_book(book_id, user_id)
        doc_context = prompts.build_doc_context([p for p in book.pages if not p.del_yn])

        # 이전 튜터 대화(기출 퀴즈 포함)를 전달해 같은 퀴즈 반복 출제를 방지
        session = await self._get_or_create_session(user_id, book_id, SESSION_TUTOR)
        history = self._history(await self.repo.list_messages(session.id))

        raw = await self._generate_ai(
            prompts.build_quiz_prompt(doc_context, history), temperature=1.2
        )
        quiz = prompts.strip_tags(raw)
        if not quiz:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"code": "AI_RESPONSE_INVALID", "message": "퀴즈를 생성하지 못했습니다."},
            )

        message = await self._add_message(session.id, user_id, "AI", quiz)
        progress = await self._add_xp(user_id, XP_QUIZ, is_correct=True)
        await self.db.commit()
        return QuizResponse(
            message=ChatMessageResponse.model_validate(message),
            progress=StudyProgressResponse.from_model(progress),
        )
