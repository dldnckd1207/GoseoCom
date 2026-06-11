"""SFR-205 수동 검증 스크립트

사용법:
    cd apps/server
    uv run python scripts/verify_sfr205.py

검증 시나리오:
    A) SKIPPED 케이스 (이미지 없음)
    B) SKIPPED 케이스 (book_id 있음)
    C) COMPLETED 케이스 (이미지 있음, 실제 OCR+번역)
"""

import asyncio
import sys
from pathlib import Path

# 프로젝트 루트를 Python path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.board.auto_reply_pipeline import run_auto_reply_batch
from app.board.models import Board, Comment, Post
from app.config import settings
from app.core.common.id_generator import next_id
from app.core.files.models import File, FileMap
from app.core.user.models import User
from app.db.session import AsyncSessionLocal
from app.translate.models import Book, PipelineRun

AI_USER = settings.ai_agent_user_id
SAMPLE_IMAGE = Path(__file__).parent / "sample_gobook.jpg"


async def _ensure_sample_image() -> str:
    """테스트용 샘플 이미지가 없으면 경로 안내."""
    if SAMPLE_IMAGE.exists():
        return str(SAMPLE_IMAGE)
    print(f"\n⚠️  샘플 이미지 없음: {SAMPLE_IMAGE}")
    print("   고서 이미지를 해당 경로에 저장하거나 아래 경로를 수정하세요.")
    print("   시나리오 C(실제 OCR+번역)는 건너뜁니다.\n")
    return ""


async def _create_test_board(db: AsyncSession, *, pipeline_enabled: bool) -> Board:
    now = datetime.now(UTC)
    board = Board(
        id=await next_id("BRD_", db),
        board_code=f"sfr205_verify_{uuid.uuid4().hex[:6]}",
        board_name=f"SFR-205 검증 게시판 (pipeline={pipeline_enabled})",
        board_type="LIST",
        read_yn=True,
        guest_read_yn=True,
        write_yn=True,
        guest_write_yn=False,
        notice_yn=False,
        reply_yn=False,
        comment_yn=True,
        secret_yn=False,
        like_yn=False,
        category_yn=False,
        attach_yn=True,
        attach_size=10240,
        attach_count=5,
        list_count=20,
        auto_reply_enabled=True,
        auto_reply_delay_min=0,
        pipeline_enabled=pipeline_enabled,
        sort_order=99,
        use_yn=True,
        created_at=now,
        created_by=AI_USER,
        updated_at=now,
        updated_by=AI_USER,
    )
    db.add(board)
    await db.commit()
    await db.refresh(board)
    return board


async def _create_test_user(db: AsyncSession) -> User:
    now = datetime.now(UTC)
    user_id = await next_id("USR_", db)
    user = User(
        id=user_id,
        email=f"verify_{uuid.uuid4().hex[:6]}@test.com",
        name="SFR205_검증유저",
        user_level=10,
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


async def _create_test_post(
    db: AsyncSession, board_id: str, user_id: str, *, book_id: str | None = None
) -> Post:
    now = datetime.now(UTC) - __import__("datetime").timedelta(minutes=1)
    post = Post(
        id=await next_id("POST_", db),
        board_id=board_id,
        user_id=user_id,
        author_name="검증유저",
        title="SFR-205 검증 게시글",
        content="이 고서의 내용을 해독해주세요.",
        auto_reply_status="PENDING",
        comment_count=0,
        book_id=book_id,
        created_at=now,
        created_by=user_id,
        updated_at=now,
        updated_by=user_id,
    )
    db.add(post)
    await db.commit()
    await db.refresh(post)
    return post


async def _attach_image(db: AsyncSession, post_id: str, user_id: str, local_path: str) -> None:
    now = datetime.now(UTC)
    file = File(
        id=await next_id("FILE_", db),
        uuid=str(uuid.uuid4()),
        original_name="gobook_sample.jpg",
        stored_name="gobook_sample.jpg",
        url_path="/files/gobook_sample.jpg",
        local_path=local_path,
        file_size=Path(local_path).stat().st_size,
        file_ext="jpg",
        mime_type="image/jpeg",
        upload_type="FORM",
        created_at=now,
        created_by=user_id,
        updated_at=now,
        updated_by=user_id,
    )
    db.add(file)
    await db.flush()
    file_map = FileMap(
        id=await next_id("FMAP_", db),
        file_id=file.id,
        target_type="POST",
        target_id=post_id,
        file_group="attachment",
        sort_order=0,
        created_at=now,
        created_by=user_id,
        updated_at=now,
        updated_by=user_id,
    )
    db.add(file_map)
    await db.commit()


async def _print_result(db: AsyncSession, post_id: str, scenario: str) -> None:
    post_r = await db.execute(select(Post).where(Post.id == post_id))
    post = post_r.scalar_one()

    run_r = await db.execute(
        select(PipelineRun).where(
            PipelineRun.post_id == post_id, PipelineRun.trigger_type == "AUTO_REPLY"
        )
    )
    run = run_r.scalar_one_or_none()

    comment_r = await db.execute(
        select(Comment).where(Comment.post_id == post_id, Comment.user_id == AI_USER)
    )
    comment = comment_r.scalar_one_or_none()

    status_icon = {"COMPLETED": "✅", "SKIPPED": "⏭️", "FAILED": "❌", "PENDING": "⏳"}.get(
        post.auto_reply_status, "❓"
    )
    print(f"\n{status_icon} [{scenario}] post_id={post_id}")
    print(f"   auto_reply_status : {post.auto_reply_status}")
    print(f"   PipelineRun       : {run.status if run else '없음'}")
    if comment:
        preview = comment.content[:120].replace("\n", " | ")
        print(f"   댓글 내용 (앞120자): {preview}")
    else:
        print("   댓글               : 없음")


async def main() -> None:
    print("=" * 60)
    print("SFR-205 파이프라인 자동 연동 검증")
    print("=" * 60)

    image_path = await _ensure_sample_image()

    async with AsyncSessionLocal() as db:
        user = await _create_test_user(db)

        # ── 시나리오 A: pipeline_enabled=false → 기존 SFR-104 경로 ──
        board_text = await _create_test_board(db, pipeline_enabled=False)
        post_a = await _create_test_post(db, board_text.id, user.id)

        # ── 시나리오 B-1: pipeline_enabled=true + book_id 있음 → SKIPPED ──
        board_pipe = await _create_test_board(db, pipeline_enabled=True)

        book = Book(
            id=await next_id("BOOK_", db),
            owner_user_id=user.id,
            title="테스트 고서",
            book_type="QUICK",
            source_type="IMAGE",
            total_pages=1,
            status="COMPLETED",
            created_at=datetime.now(UTC),
            created_by=user.id,
            updated_at=datetime.now(UTC),
            updated_by=user.id,
        )
        db.add(book)
        await db.commit()
        await db.refresh(book)

        post_b1 = await _create_test_post(db, board_pipe.id, user.id, book_id=book.id)

        # ── 시나리오 B-2: pipeline_enabled=true + 이미지 없음 → SKIPPED ──
        post_b2 = await _create_test_post(db, board_pipe.id, user.id)

        # ── 시나리오 C: pipeline_enabled=true + 이미지 있음 → OCR+번역 ──
        post_c = None
        if image_path:
            post_c = await _create_test_post(db, board_pipe.id, user.id)
            await _attach_image(db, post_c.id, user.id, image_path)

    print("\n📋 스케줄러 배치 실행 중...")
    await run_auto_reply_batch()
    print("   완료")

    async with AsyncSessionLocal() as db:
        await _print_result(db, post_a.id, "A: pipeline_enabled=false (텍스트 자동 답변)")
        await _print_result(
            db, post_b1.id, "B-1: pipeline_enabled=true + book_id 있음 (SKIPPED 예상)"
        )
        await _print_result(
            db, post_b2.id, "B-2: pipeline_enabled=true + 이미지 없음 (SKIPPED 예상)"
        )
        if post_c:
            await _print_result(
                db, post_c.id, "C: pipeline_enabled=true + 이미지 있음 (OCR+번역 예상)"
            )

    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
