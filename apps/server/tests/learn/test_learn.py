"""learn-workspace: 학습하기 (Beta) — AI 학습 워크스페이스 테스트"""

import json
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.common.id_generator import next_id
from app.core.security import create_access_token
from app.core.user.models import User
from app.learn import prompts
from app.learn.models import LearnStudyProgress
from app.learn.service import KST
from app.translate.models import Book, BookPage
from tests.conftest import unique_email

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _create_user(db: AsyncSession, user_level: int = 10) -> User:
    user_id = await next_id("USR_", db)
    now = datetime.now(UTC)
    user = User(
        id=user_id,
        email=unique_email(),
        name=f"테스트유저_{user_id[-4:]}",
        user_level=user_level,
        joined_at=now,
        created_at=now,
        created_by=user_id,
        updated_at=now,
        updated_by=user_id,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def _create_completed_book(
    db: AsyncSession, owner_id: str, status: str = "COMPLETED"
) -> Book:
    now = datetime.now(UTC)
    book = Book(
        id=await next_id("BOOK_", db),
        owner_user_id=owner_id,
        title="고서.png",
        book_type="QUICK",
        source_type="IMAGE",
        total_pages=1,
        status=status,
        summary_text="불교 관련 고문서 요약",
        keywords=[{"word": "真身", "reading": "진신", "meaning": "고승의 육신", "count": 2}],
        created_at=now,
        created_by=owner_id,
        updated_at=now,
        updated_by=owner_id,
    )
    db.add(book)
    page = BookPage(
        id=await next_id("BPAGE_", db),
        book_id=book.id,
        page_no=1,
        ocr_text="宋大祖國之初王師干南海",
        literal_text="송나라 태조 초기 왕사가 남해를 정벌하였다.",
        interpretive_text="송나라 초기 불교 문화 관련 기록이다.",
        status="COMPLETED",
        created_at=now,
        created_by=owner_id,
        updated_at=now,
        updated_by=owner_id,
    )
    db.add(page)
    await db.commit()
    await db.refresh(book)
    return book


def _login(auth_client: AsyncClient, user: User) -> None:
    token = create_access_token(user.id, user_level=10, user_name=user.name)
    auth_client.cookies.set("access_token", token)


_FLASHCARDS_JSON = json.dumps(
    [{"term": f"用語{i}", "meaning": f"뜻풀이 {i}", "type": "단어 카드"} for i in range(1, 6)],
    ensure_ascii=False,
)


# ---------------------------------------------------------------------------
# 워크스페이스 부트스트랩
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_workspace_success(auth_client: AsyncClient, db: AsyncSession) -> None:
    user = await _create_user(db)
    book = await _create_completed_book(db, user.id)
    _login(auth_client, user)

    response = await auth_client.get(f"/api/v1/learn/books/{book.id}")
    assert response.status_code == 200
    body = response.json()
    assert body["header"]["success"] is True
    data = body["body"]["data"]
    assert data["book_id"] == book.id
    assert len(data["pages"]) == 1
    assert data["pages"][0]["ocr_text"] == "宋大祖國之初王師干南海"
    assert data["chat_messages"] == []
    assert data["tutor_messages"] == []
    assert data["flashcards"] == []
    assert data["progress"]["level"] == 1
    assert data["progress"]["xp"] == 0


@pytest.mark.asyncio
async def test_workspace_forbidden_other_user(auth_client: AsyncClient, db: AsyncSession) -> None:
    owner = await _create_user(db)
    other = await _create_user(db)
    book = await _create_completed_book(db, owner.id)
    _login(auth_client, other)

    response = await auth_client.get(f"/api/v1/learn/books/{book.id}")
    assert response.status_code == 403
    assert response.json()["header"]["code"] == "FORBIDDEN"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("method", "path", "body"),
    [
        ("POST", "chat", {"question": "질문"}),
        ("POST", "tutor", {"question": "질문"}),
        ("POST", "summary", None),
        ("POST", "flashcards", None),
        ("POST", "flashcards/review", {"result": "KNOWN"}),
        ("POST", "quiz", None),
    ],
)
async def test_all_endpoints_forbidden_other_user(
    auth_client: AsyncClient, db: AsyncSession, method: str, path: str, body: dict[str, str] | None
) -> None:
    """소유권 검사 회귀 방어 — 모든 엔드포인트가 타인 book에 403을 반환해야 한다."""
    owner = await _create_user(db)
    other = await _create_user(db)
    book = await _create_completed_book(db, owner.id)
    _login(auth_client, other)

    with patch("app.learn.prompts.generate", new=AsyncMock(return_value="응답")):
        response = await auth_client.request(
            method, f"/api/v1/learn/books/{book.id}/{path}", json=body
        )
    assert response.status_code == 403
    assert response.json()["header"]["code"] == "FORBIDDEN"


@pytest.mark.asyncio
async def test_workspace_not_found(auth_client: AsyncClient, db: AsyncSession) -> None:
    user = await _create_user(db)
    _login(auth_client, user)

    response = await auth_client.get("/api/v1/learn/books/BOOK_99999999")
    assert response.status_code == 404
    assert response.json()["header"]["code"] == "BOOK_NOT_FOUND"


@pytest.mark.asyncio
async def test_workspace_not_completed(auth_client: AsyncClient, db: AsyncSession) -> None:
    user = await _create_user(db)
    book = await _create_completed_book(db, user.id, status="TRANSLATING")
    _login(auth_client, user)

    response = await auth_client.get(f"/api/v1/learn/books/{book.id}")
    assert response.status_code == 400
    assert response.json()["header"]["code"] == "BOOK_NOT_COMPLETED"


# ---------------------------------------------------------------------------
# 문서 Q&A 챗봇 / 튜터
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_chat_persists_user_and_ai_messages(
    auth_client: AsyncClient, db: AsyncSession
) -> None:
    user = await _create_user(db)
    book = await _create_completed_book(db, user.id)
    _login(auth_client, user)

    with patch(
        "app.learn.prompts.generate", new=AsyncMock(return_value="真身은 고승의 육신입니다.")
    ):
        response = await auth_client.post(
            f"/api/v1/learn/books/{book.id}/chat", json={"question": "真身의 의미는?"}
        )
    assert response.status_code == 200
    data = response.json()["body"]["data"]
    assert data["user_message"]["role"] == "USER"
    assert data["user_message"]["content"] == "真身의 의미는?"
    assert data["ai_message"]["role"] == "AI"
    assert data["progress"] is None  # 문서 Q&A는 XP 미적립

    # 재조회 시 대화 기록 복원 (세션 재사용)
    workspace = await auth_client.get(f"/api/v1/learn/books/{book.id}")
    messages = workspace.json()["body"]["data"]["chat_messages"]
    assert len(messages) == 2
    assert [m["role"] for m in messages] == ["USER", "AI"]


@pytest.mark.asyncio
async def test_tutor_awards_xp(auth_client: AsyncClient, db: AsyncSession) -> None:
    user = await _create_user(db)
    book = await _create_completed_book(db, user.id)
    _login(auth_client, user)

    with patch("app.learn.prompts.generate", new=AsyncMock(return_value="좋은 질문이에요.")):
        response = await auth_client.post(
            f"/api/v1/learn/books/{book.id}/tutor", json={"question": "守塔僧의 역할은?"}
        )
    assert response.status_code == 200
    data = response.json()["body"]["data"]
    assert data["progress"]["xp"] == 10
    assert data["progress"]["streak"] == 1


@pytest.mark.asyncio
async def test_chat_question_validation(auth_client: AsyncClient, db: AsyncSession) -> None:
    user = await _create_user(db)
    book = await _create_completed_book(db, user.id)
    _login(auth_client, user)

    response = await auth_client.post(f"/api/v1/learn/books/{book.id}/chat", json={"question": ""})
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# AI 요약 + 학습 분석
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_summary_returns_analysis_items(auth_client: AsyncClient, db: AsyncSession) -> None:
    user = await _create_user(db)
    book = await _create_completed_book(db, user.id)
    _login(auth_client, user)

    ai_json = json.dumps(
        {"summary": "불교 고문서 요약.", "analysis": ["포인트1", "포인트2", "포인트3", "포인트4"]},
        ensure_ascii=False,
    )
    with patch("app.learn.prompts.generate", new=AsyncMock(return_value=ai_json)):
        response = await auth_client.post(f"/api/v1/learn/books/{book.id}/summary")
    assert response.status_code == 200
    data = response.json()["body"]["data"]
    assert data["summary"] == "불교 고문서 요약."
    assert len(data["analysis_items"]) == 3  # 최대 3개로 절단


# ---------------------------------------------------------------------------
# 암기 카드
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_flashcards_generate(auth_client: AsyncClient, db: AsyncSession) -> None:
    user = await _create_user(db)
    book = await _create_completed_book(db, user.id)
    _login(auth_client, user)

    with patch("app.learn.prompts.generate", new=AsyncMock(return_value=_FLASHCARDS_JSON)):
        response = await auth_client.post(f"/api/v1/learn/books/{book.id}/flashcards")
    assert response.status_code == 201
    body = response.json()
    assert body["header"]["code"] == "CREATED"
    data = body["body"]["data"]
    assert len(data["cards"]) == 5
    assert data["cards"][0]["term"] == "用語1"
    assert data["progress"]["xp"] == 20


@pytest.mark.asyncio
async def test_flashcards_regenerate_replaces_set(
    auth_client: AsyncClient, db: AsyncSession
) -> None:
    user = await _create_user(db)
    book = await _create_completed_book(db, user.id)
    _login(auth_client, user)

    with patch("app.learn.prompts.generate", new=AsyncMock(return_value=_FLASHCARDS_JSON)):
        await auth_client.post(f"/api/v1/learn/books/{book.id}/flashcards")
        await auth_client.post(f"/api/v1/learn/books/{book.id}/flashcards")

    workspace = await auth_client.get(f"/api/v1/learn/books/{book.id}")
    cards = workspace.json()["body"]["data"]["flashcards"]
    assert len(cards) == 5  # 기존 세트는 soft delete로 교체


@pytest.mark.asyncio
async def test_flashcard_review_rotation_and_xp(auth_client: AsyncClient, db: AsyncSession) -> None:
    user = await _create_user(db)
    book = await _create_completed_book(db, user.id)
    _login(auth_client, user)

    with patch("app.learn.prompts.generate", new=AsyncMock(return_value=_FLASHCARDS_JSON)):
        await auth_client.post(f"/api/v1/learn/books/{book.id}/flashcards")  # +20 XP

    response = await auth_client.post(
        f"/api/v1/learn/books/{book.id}/flashcards/review", json={"result": "KNOWN"}
    )
    assert response.status_code == 200
    data = response.json()["body"]["data"]
    assert data["active_card"]["term"] == "用語2"  # 첫 카드가 맨 뒤로 회전
    assert data["progress"]["xp"] == 28  # 20 + 8

    response = await auth_client.post(
        f"/api/v1/learn/books/{book.id}/flashcards/review", json={"result": "NEXT"}
    )
    data = response.json()["body"]["data"]
    assert data["active_card"]["term"] == "用語3"
    assert data["progress"]["xp"] == 31  # 28 + 3
    # 활동 3회 중 정답 2회 (카드 생성 + KNOWN) → 67%
    assert data["progress"]["accuracy"] == 67


@pytest.mark.asyncio
async def test_flashcard_review_single_card_stays_active(
    auth_client: AsyncClient, db: AsyncSession
) -> None:
    """카드가 1개면 회전 없이 같은 카드가 유지되고 known_yn만 갱신된다."""
    user = await _create_user(db)
    book = await _create_completed_book(db, user.id)
    _login(auth_client, user)

    single_card = json.dumps([{"term": "真身", "meaning": "고승의 육신", "type": "단어 카드"}])
    with patch("app.learn.prompts.generate", new=AsyncMock(return_value=single_card)):
        await auth_client.post(f"/api/v1/learn/books/{book.id}/flashcards")

    response = await auth_client.post(
        f"/api/v1/learn/books/{book.id}/flashcards/review", json={"result": "KNOWN"}
    )
    assert response.status_code == 200
    data = response.json()["body"]["data"]
    assert data["active_card"]["term"] == "真身"
    assert data["active_card"]["known_yn"] is True
    assert data["progress"]["xp"] == 28  # 20 + 8


@pytest.mark.asyncio
async def test_flashcard_review_without_cards(auth_client: AsyncClient, db: AsyncSession) -> None:
    user = await _create_user(db)
    book = await _create_completed_book(db, user.id)
    _login(auth_client, user)

    response = await auth_client.post(
        f"/api/v1/learn/books/{book.id}/flashcards/review", json={"result": "KNOWN"}
    )
    assert response.status_code == 404
    assert response.json()["header"]["code"] == "FLASHCARD_NOT_FOUND"


# ---------------------------------------------------------------------------
# 문맥 퀴즈
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_quiz_appends_tutor_message(auth_client: AsyncClient, db: AsyncSession) -> None:
    user = await _create_user(db)
    book = await _create_completed_book(db, user.id)
    _login(auth_client, user)

    with patch(
        "app.learn.prompts.generate",
        new=AsyncMock(return_value="퀴즈: 守塔僧의 역할은? 답: 탑을 관리하는 승려."),
    ):
        response = await auth_client.post(f"/api/v1/learn/books/{book.id}/quiz")
    assert response.status_code == 200
    data = response.json()["body"]["data"]
    assert data["message"]["role"] == "AI"
    assert data["progress"]["xp"] == 15

    workspace = await auth_client.get(f"/api/v1/learn/books/{book.id}")
    tutor_messages = workspace.json()["body"]["data"]["tutor_messages"]
    assert len(tutor_messages) == 1


@pytest.mark.asyncio
async def test_quiz_strips_model_tags(auth_client: AsyncClient, db: AsyncSession) -> None:
    user = await _create_user(db)
    book = await _create_completed_book(db, user.id)
    _login(auth_client, user)

    with patch(
        "app.learn.prompts.generate",
        new=AsyncMock(return_value="<question>守塔僧의 역할은 무엇일까요?</question>"),
    ):
        response = await auth_client.post(f"/api/v1/learn/books/{book.id}/quiz")
    assert response.status_code == 200
    content = response.json()["body"]["data"]["message"]["content"]
    assert "<question>" not in content
    assert content == "守塔僧의 역할은 무엇일까요?"


# ---------------------------------------------------------------------------
# 학습 진행도 (streak / XP)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_streak_same_day_not_incremented(auth_client: AsyncClient, db: AsyncSession) -> None:
    """같은 날(KST) 여러 번 활동해도 streak은 1 유지."""
    user = await _create_user(db)
    book = await _create_completed_book(db, user.id)
    _login(auth_client, user)

    with patch("app.learn.prompts.generate", new=AsyncMock(return_value="답변")):
        await auth_client.post(f"/api/v1/learn/books/{book.id}/tutor", json={"question": "1"})
        response = await auth_client.post(
            f"/api/v1/learn/books/{book.id}/tutor", json={"question": "2"}
        )
    data = response.json()["body"]["data"]
    assert data["progress"]["streak"] == 1
    assert data["progress"]["xp"] == 20  # 10 + 10


@pytest.mark.asyncio
async def test_streak_increments_on_new_kst_day(auth_client: AsyncClient, db: AsyncSession) -> None:
    """마지막 학습일이 어제(KST)면 streak이 증가한다."""
    user = await _create_user(db)
    book = await _create_completed_book(db, user.id)
    _login(auth_client, user)

    with patch("app.learn.prompts.generate", new=AsyncMock(return_value="답변")):
        await auth_client.post(f"/api/v1/learn/books/{book.id}/tutor", json={"question": "1"})

    # 마지막 학습일을 어제로 되돌려 날짜 경계를 시뮬레이션
    result = await db.execute(
        select(LearnStudyProgress).where(LearnStudyProgress.user_id == user.id)
    )
    progress = result.scalar_one()
    progress.last_study_date = datetime.now(UTC).astimezone(KST).date() - timedelta(days=1)
    await db.commit()

    with patch("app.learn.prompts.generate", new=AsyncMock(return_value="답변")):
        response = await auth_client.post(
            f"/api/v1/learn/books/{book.id}/tutor", json={"question": "2"}
        )
    assert response.json()["body"]["data"]["progress"]["streak"] == 2


# ---------------------------------------------------------------------------
# 프롬프트 엣지 케이스 (단위)
# ---------------------------------------------------------------------------


def _make_page(
    page_no: int, ocr: str, literal: str = "직역", interpretive: str = "의역"
) -> BookPage:
    return BookPage(
        page_no=page_no, ocr_text=ocr, literal_text=literal, interpretive_text=interpretive
    )


def test_doc_context_truncated_to_max_chars() -> None:
    page = _make_page(1, "宋" * 9000)
    context = prompts.build_doc_context([page])
    assert len(context) <= prompts.DOC_CONTEXT_MAX_CHARS


def test_doc_context_orders_pages_by_page_no() -> None:
    pages = [_make_page(2, "둘째 페이지"), _make_page(1, "첫째 페이지")]
    context = prompts.build_doc_context(pages)
    assert context.index("[페이지 1]") < context.index("[페이지 2]")


def test_chat_prompt_history_limited_to_recent_10() -> None:
    history = [("USER", f"질문{i}") for i in range(12)]
    prompt = prompts.build_chat_prompt("문서", history, "마지막 질문")
    assert "질문0" not in prompt
    assert "질문1\n" not in prompt
    assert "질문2" in prompt
    assert "질문11" in prompt


# ---------------------------------------------------------------------------
# AI 에러 매핑
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_chat_ai_timeout_returns_500_with_code(
    auth_client: AsyncClient, db: AsyncSession
) -> None:
    user = await _create_user(db)
    book = await _create_completed_book(db, user.id)
    _login(auth_client, user)

    with patch("app.learn.prompts.generate", new=AsyncMock(side_effect=TimeoutError())):
        response = await auth_client.post(
            f"/api/v1/learn/books/{book.id}/chat", json={"question": "질문"}
        )
    assert response.status_code == 500
    assert response.json()["header"]["code"] == "AI_TIMEOUT"


@pytest.mark.asyncio
async def test_flashcards_invalid_ai_response(auth_client: AsyncClient, db: AsyncSession) -> None:
    user = await _create_user(db)
    book = await _create_completed_book(db, user.id)
    _login(auth_client, user)

    with patch("app.learn.prompts.generate", new=AsyncMock(return_value="JSON이 아닌 응답")):
        response = await auth_client.post(f"/api/v1/learn/books/{book.id}/flashcards")
    assert response.status_code == 500
    assert response.json()["header"]["code"] == "AI_RESPONSE_INVALID"
