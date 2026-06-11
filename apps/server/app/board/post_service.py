"""게시글 Service — 비즈니스 로직"""

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.board.models import Board, Post, PostHistory
from app.board.post_repository import PostHistoryRepository, PostRepository
from app.board.post_schemas import (
    AdminPostDetailResponse,
    AdminPostListRequest,
    AdminPostSummaryResponse,
    PostBookData,
    PostBookPageData,
    PostCreateRequest,
    PostDetailResponse,
    PostListRequest,
    PostSummaryResponse,
    PostUpdateRequest,
)
from app.board.repository import BoardRepository
from app.config import settings
from app.core.common.id_generator import next_id
from app.core.common.response import PageData
from app.core.files.models import File, FileMap
from app.core.files.repository import FileMapRepository, FileRepository
from app.core.files.schemas import FileResponse, FileUploadResponse
from app.core.files.service import FileService
from app.core.user.models import User
from app.translate.models import Book
from app.translate.repository import BookRepository


def _is_ai_gen(user_id: str) -> bool:
    return user_id == settings.ai_agent_user_id


def _to_summary(
    post: Post, board_code: str, category_name: str | None = None
) -> PostSummaryResponse:
    return PostSummaryResponse(
        id=post.id,
        board_id=post.board_id,
        board_code=board_code,
        author_name=post.author_name,
        is_ai_gen=_is_ai_gen(post.user_id),
        title=post.title,
        notice_yn=post.notice_yn,
        view_count=post.view_count,
        comment_count=post.comment_count,
        created_at=post.created_at,
        category_id=post.category_id,
        category_name=category_name,
    )


def _to_admin_summary(post: Post, deleted_by_name: str | None = None) -> AdminPostSummaryResponse:
    return AdminPostSummaryResponse(
        id=post.id,
        board_id=post.board_id,
        board_code=post.board.board_code if post.board else "",
        board_name=post.board.board_name if post.board else "",
        category_id=post.category_id,
        category_name=post.category.category_name if post.category else None,
        user_id=post.user_id,
        author_name=post.author_name,
        is_ai_gen=_is_ai_gen(post.user_id),
        title=post.title,
        notice_yn=post.notice_yn,
        view_count=post.view_count,
        comment_count=post.comment_count,
        auto_reply_status=post.auto_reply_status,
        del_yn=post.del_yn,
        deleted_at=post.deleted_at,
        deleted_by=post.deleted_by,
        deleted_by_name=deleted_by_name,
        created_at=post.created_at,
        updated_at=post.updated_at,
    )


def _to_post_book_data(book: Book) -> PostBookData:
    source_file_url = book.source_file.url_path if book.source_file else None
    return PostBookData(
        book_id=book.id,
        title=book.title,
        source_file_url=source_file_url,
        summary_text=book.summary_text,
        keywords=book.keywords,
        pages=[
            PostBookPageData(
                page_no=p.page_no,
                ocr_text=p.ocr_text,
                literal_text=p.literal_text,
                interpretive_text=p.interpretive_text,
            )
            for p in sorted(book.pages, key=lambda x: x.page_no)
        ],
    )


def _to_detail(
    post: Post,
    board_code: str,
    files: list[FileResponse],
    category_name: str | None = None,
    book: PostBookData | None = None,
) -> PostDetailResponse:
    return PostDetailResponse(
        id=post.id,
        board_id=post.board_id,
        board_code=board_code,
        user_id=post.user_id,
        author_name=post.author_name,
        is_ai_gen=_is_ai_gen(post.user_id),
        parent_id=post.parent_id,
        depth=post.depth,
        title=post.title,
        content=post.content,
        notice_yn=post.notice_yn,
        view_count=post.view_count,
        comment_count=post.comment_count,
        auto_reply_status=post.auto_reply_status,
        files=files,
        created_at=post.created_at,
        updated_at=post.updated_at,
        category_id=post.category_id,
        category_name=category_name,
        book=book,
    )


def _to_admin_detail(
    post: Post,
    files: list[FileResponse],
    book: PostBookData | None = None,
    deleted_by_name: str | None = None,
) -> AdminPostDetailResponse:
    summary = _to_admin_summary(post, deleted_by_name=deleted_by_name)
    return AdminPostDetailResponse(
        **summary.model_dump(),
        content=post.content,
        parent_id=post.parent_id,
        depth=post.depth,
        files=files,
        book=book,
    )


class PostService:
    def __init__(self, db: AsyncSession) -> None:
        self.repo = PostRepository(db)
        self.history_repo = PostHistoryRepository(db)
        self.board_repo = BoardRepository(db)
        self.file_repo = FileRepository(db)
        self.file_map_repo = FileMapRepository(db)
        self.book_repo = BookRepository(db)
        self.db = db

    # ------------------------------------------------------------------
    # 조회
    # ------------------------------------------------------------------

    async def list_posts(
        self, req: PostListRequest, payload: dict[str, Any]
    ) -> PageData[PostSummaryResponse]:
        boards = await self.board_repo.get_by_codes(req.board_codes)
        if not boards:
            return PageData(items=[], total=0, page=req.page, size=req.size)

        # board_group 없는 게시판(개별 게시판)은 기존 권한 정책 적용
        # board_group 있는 게시판(커뮤니티 등)은 목록까지 허용, 상세에서만 체크
        for board in boards:
            if board.board_group is None:
                self._check_read_permission(board, payload)

        board_map = {b.id: b.board_code for b in boards}
        board_ids = list(board_map.keys())

        posts, total = await self.repo.list_by_boards(board_ids, req.keyword, req.page, req.size)
        return PageData(
            items=[
                _to_summary(
                    p,
                    board_map.get(p.board_id, ""),
                    category_name=p.category.category_name if p.category else None,
                )
                for p in posts
            ],
            total=total,
            page=req.page,
            size=req.size,
        )

    async def get_post(self, post_id: str, payload: dict[str, Any]) -> PostDetailResponse:
        post = await self._get_post(post_id)
        board = await self._get_board_by_id(post.board_id)
        self._check_read_permission(board, payload)

        category_name = post.category.category_name if post.category else None

        await self.repo.update_view_count(post_id)
        await self.db.commit()
        await self.db.refresh(post)

        file_maps = await self.file_map_repo.list_by_target("POST", post_id)
        files = await self._build_file_responses(file_maps)

        book_data: PostBookData | None = None
        if post.book_id:
            book = await self.book_repo.get_by_id_with_pages(post.book_id)
            if book:
                book_data = _to_post_book_data(book)

        return _to_detail(
            post, board.board_code, files, category_name=category_name, book=book_data
        )

    async def admin_list_posts(
        self, req: AdminPostListRequest
    ) -> PageData[AdminPostSummaryResponse]:
        posts, total = await self.repo.admin_list(
            keyword=req.keyword,
            board_id=req.board_id,
            author_keyword=req.author_keyword,
            notice_yn=req.notice_yn,
            deleted_status=req.deleted_status,
            page=req.page,
            size=req.size,
        )
        return PageData(
            items=[_to_admin_summary(post) for post in posts],
            total=total,
            page=req.page,
            size=req.size,
        )

    async def admin_get_post(self, post_id: str) -> AdminPostDetailResponse:
        post = await self._get_admin_post(post_id)
        file_maps = await self.file_map_repo.list_by_target("POST", post_id)
        files = await self._build_file_responses(file_maps)
        book_data: PostBookData | None = None
        if post.book_id:
            book = await self.book_repo.get_by_id_with_pages(post.book_id)
            if book:
                book_data = _to_post_book_data(book)
        deleted_by_name = await self._get_user_name(post.deleted_by)
        return _to_admin_detail(post, files, book=book_data, deleted_by_name=deleted_by_name)

    # ------------------------------------------------------------------
    # 작성
    # ------------------------------------------------------------------

    async def create_post(
        self, req: PostCreateRequest, payload: dict[str, Any]
    ) -> PostDetailResponse:
        user_id: str = payload["sub"]
        user_level: int = payload["level"]
        author_name: str = payload.get("name", "")

        board = await self._get_board_by_code(req.board_code)

        if not board.write_yn:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "BOARD_WRITE_FORBIDDEN",
                    "message": "글 작성이 허용되지 않는 게시판입니다.",
                },
            )
        if req.notice_yn:
            if not board.notice_yn:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={"code": "FORBIDDEN", "message": "공지 기능이 비활성화된 게시판입니다."},
                )
            if user_level < 70:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={"code": "FORBIDDEN", "message": "공지 설정은 관리자만 가능합니다."},
                )

        depth = 0
        if req.parent_id:
            if not board.reply_yn:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "code": "REPLY_NOT_ALLOWED",
                        "message": "답글이 허용되지 않는 게시판입니다.",
                    },
                )
            parent = await self.repo.get_by_id(req.parent_id)
            if not parent or parent.board_id != board.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "code": "REPLY_NOT_ALLOWED",
                        "message": "답글 대상 게시글을 찾을 수 없습니다.",
                    },
                )
            if parent.depth != 0:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "code": "REPLY_NOT_ALLOWED",
                        "message": "답글의 답글은 허용되지 않습니다.",
                    },
                )
            depth = 1

        file_ids = list(dict.fromkeys(req.file_ids))
        files_entities = await self._validate_files(file_ids, board, user_id, user_level)

        category_name: str | None = None
        if req.category_id:
            if not board.category_yn:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "code": "CATEGORY_NOT_ALLOWED",
                        "message": "이 게시판은 카테고리를 지원하지 않습니다.",
                    },
                )
            category = await self.board_repo.get_category_by_id(req.category_id)
            if not category or category.board_id != board.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"code": "INVALID_CATEGORY", "message": "유효하지 않은 카테고리입니다."},
                )
            category_name = category.category_name

        if req.book_id:
            book = await self.book_repo.get_by_id(req.book_id)
            if not book:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={"code": "BOOK_NOT_FOUND", "message": "번역 이력을 찾을 수 없습니다."},
                )
            if book.owner_user_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "code": "FORBIDDEN",
                        "message": "본인의 번역 이력만 연동할 수 있습니다.",
                    },
                )
            if book.status != "COMPLETED":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "code": "INVALID_BOOK_STATUS",
                        "message": "완료된 번역 이력만 연동할 수 있습니다.",
                    },
                )

        now = datetime.now(UTC)
        auto_reply_status = (
            "SKIPPED" if req.book_id else ("PENDING" if board.auto_reply_enabled else "SKIPPED")
        )
        post = Post(
            id=await next_id("POST_", self.db),
            board_id=board.id,
            category_id=req.category_id,
            user_id=user_id,
            author_name=author_name,
            parent_id=req.parent_id,
            depth=depth,
            title=req.title,
            content=req.content,
            notice_yn=req.notice_yn,
            book_id=req.book_id,
            auto_reply_status=auto_reply_status,
            created_at=now,
            created_by=user_id,
            updated_at=now,
            updated_by=user_id,
        )
        created = await self.repo.create(post)

        for i, file_entity in enumerate(files_entities):
            await self.file_map_repo.upsert(
                file_entity.id, "POST", created.id, user_id, sort_order=i
            )

        await self.db.commit()
        await self.db.refresh(created)

        file_responses = [
            FileResponse(
                file_id=f.id,
                original_name=f.original_name,
                url_path=f.url_path,
                file_size=f.file_size,
                file_ext=f.file_ext,
            )
            for f in files_entities
        ]
        return _to_detail(created, board.board_code, file_responses, category_name=category_name)

    # ------------------------------------------------------------------
    # 수정
    # ------------------------------------------------------------------

    async def update_post(
        self, post_id: str, req: PostUpdateRequest, payload: dict[str, Any]
    ) -> PostDetailResponse:
        user_id: str = payload["sub"]
        user_level: int = payload["level"]

        post = await self._get_post(post_id)
        board = await self._get_board_by_id(post.board_id)
        category_name = post.category.category_name if post.category else None

        if post.user_id != user_id and user_level < 70:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "FORBIDDEN", "message": "수정 권한이 없습니다."},
            )
        if req.notice_yn is True:
            if not board.notice_yn:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={"code": "FORBIDDEN", "message": "공지 기능이 비활성화된 게시판입니다."},
                )
            if user_level < 70:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={"code": "FORBIDDEN", "message": "공지 설정은 관리자만 가능합니다."},
                )

        file_ids = None
        files_entities: list[File] = []
        if req.file_ids is not None:
            file_ids = list(dict.fromkeys(req.file_ids))
            files_entities = await self._validate_files(file_ids, board, user_id, user_level)

        # 트랜잭션: history → post update → file_map 교체
        version = await self.history_repo.get_last_version(post_id)
        history = PostHistory(
            post_id=post_id,
            version=version + 1,
            action="UPDATE",
            title=post.title,
            content=post.content,
            changed_by=user_id,
            changed_at=datetime.now(UTC),
        )
        await self.history_repo.insert(history)

        if "book_id" in req.model_fields_set:
            if req.book_id is not None:
                book = await self.book_repo.get_by_id(req.book_id)
                if not book:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail={
                            "code": "BOOK_NOT_FOUND",
                            "message": "번역 이력을 찾을 수 없습니다.",
                        },
                    )
                if book.owner_user_id != user_id:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail={
                            "code": "FORBIDDEN",
                            "message": "본인의 번역 이력만 연동할 수 있습니다.",
                        },
                    )
                if book.status != "COMPLETED":
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail={
                            "code": "INVALID_BOOK_STATUS",
                            "message": "완료된 번역 이력만 연동할 수 있습니다.",
                        },
                    )
            post.book_id = req.book_id

        if "category_id" in req.model_fields_set:
            if req.category_id is not None:
                if not board.category_yn:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail={
                            "code": "CATEGORY_NOT_ALLOWED",
                            "message": "이 게시판은 카테고리를 지원하지 않습니다.",
                        },
                    )
                category = await self.board_repo.get_category_by_id(req.category_id)
                if not category or category.board_id != board.id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail={
                            "code": "INVALID_CATEGORY",
                            "message": "유효하지 않은 카테고리입니다.",
                        },
                    )
                category_name = category.category_name
            else:
                category_name = None
            post.category_id = req.category_id

        now = datetime.now(UTC)
        if req.title is not None:
            post.title = req.title
        if req.content is not None:
            post.content = req.content
        if req.notice_yn is not None:
            post.notice_yn = req.notice_yn
        post.updated_at = now
        post.updated_by = user_id

        if file_ids is not None:
            await self.file_map_repo.soft_delete_all_by_target("POST", post_id, deleted_by=user_id)
            for i, file_entity in enumerate(files_entities):
                await self.file_map_repo.upsert(
                    file_entity.id, "POST", post_id, user_id, sort_order=i
                )

        await self.db.commit()
        await self.db.refresh(post)

        file_maps = await self.file_map_repo.list_by_target("POST", post_id)
        file_responses = await self._build_file_responses(file_maps)

        return _to_detail(post, board.board_code, file_responses, category_name=category_name)

    # ------------------------------------------------------------------
    # 삭제
    # ------------------------------------------------------------------

    async def delete_post(self, post_id: str, payload: dict[str, Any]) -> None:
        user_id: str = payload["sub"]
        user_level: int = payload["level"]

        post = await self._get_post(post_id)
        if post.user_id != user_id and user_level < 70:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "FORBIDDEN", "message": "삭제 권한이 없습니다."},
            )

        version = await self.history_repo.get_last_version(post_id)
        history = PostHistory(
            post_id=post_id,
            version=version + 1,
            action="DELETE",
            title=post.title,
            content=post.content,
            changed_by=user_id,
            changed_at=datetime.now(UTC),
        )
        await self.history_repo.insert(history)
        await self.repo.soft_delete(post, deleted_by=user_id)
        await self.db.commit()

    async def admin_delete_post(self, post_id: str, payload: dict[str, Any]) -> None:
        user_id: str = payload["sub"]
        post = await self._get_admin_post(post_id)
        if post.del_yn:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "POST_ALREADY_DELETED", "message": "이미 삭제된 게시글입니다."},
            )

        version = await self.history_repo.get_last_version(post_id)
        history = PostHistory(
            post_id=post_id,
            version=version + 1,
            action="DELETE",
            title=post.title,
            content=post.content,
            changed_by=user_id,
            changed_at=datetime.now(UTC),
        )
        await self.history_repo.insert(history)
        await self.repo.soft_delete(post, deleted_by=user_id)
        await self.db.commit()

    async def admin_restore_post(
        self, post_id: str, payload: dict[str, Any]
    ) -> AdminPostDetailResponse:
        user_id: str = payload["sub"]
        post = await self._get_admin_post(post_id)
        if not post.del_yn:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "POST_NOT_DELETED", "message": "삭제된 게시글이 아닙니다."},
            )

        version = await self.history_repo.get_last_version(post_id)
        history = PostHistory(
            post_id=post_id,
            version=version + 1,
            action="RESTORE",
            title=post.title,
            content=post.content,
            changed_by=user_id,
            changed_at=datetime.now(UTC),
        )
        await self.history_repo.insert(history)
        await self.repo.restore(post, updated_by=user_id)
        await self.db.commit()
        await self.db.refresh(post)
        return await self.admin_get_post(post_id)

    # ------------------------------------------------------------------
    # 파일 업로드
    # ------------------------------------------------------------------

    async def upload_file(
        self, board_code: str, file: UploadFile, payload: dict[str, Any]
    ) -> FileUploadResponse:
        user_id: str = payload["sub"]
        board = await self._get_board_by_code(board_code)

        if not board.attach_yn:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "ATTACH_NOT_ALLOWED",
                    "message": "첨부파일이 허용되지 않는 게시판입니다.",
                },
            )

        file_ext = ""
        if file.filename:
            file_ext = Path(file.filename).suffix.lstrip(".").lower()

        if board.attach_ext:
            allowed = [e.strip().lower() for e in board.attach_ext.split(",")]
            if not file_ext or file_ext not in allowed:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "code": "ATTACH_EXT_NOT_ALLOWED",
                        "message": "허용되지 않는 파일 확장자입니다.",
                    },
                )

        content = await file.read()
        if len(content) > board.attach_size * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "ATTACH_SIZE_EXCEEDED",
                    "message": "파일 크기가 허용 한도를 초과했습니다.",
                },
            )

        return await FileService(self.db).upload(file, user_id, content=content)

    # ------------------------------------------------------------------
    # 내부 헬퍼
    # ------------------------------------------------------------------

    async def _get_board_by_code(self, board_code: str) -> Board:
        board = await self.board_repo.get_by_code(board_code)
        if not board:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "BOARD_NOT_FOUND", "message": "게시판을 찾을 수 없습니다."},
            )
        return board

    async def _get_board_by_id(self, board_id: str) -> Board:
        board = await self.board_repo.get_by_id(board_id)
        if not board:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "BOARD_NOT_FOUND", "message": "게시판을 찾을 수 없습니다."},
            )
        return board

    async def _get_post(self, post_id: str) -> Post:
        post = await self.repo.get_by_id(post_id)
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "POST_NOT_FOUND", "message": "게시글을 찾을 수 없습니다."},
            )
        return post

    async def _get_admin_post(self, post_id: str) -> Post:
        post = await self.repo.admin_get_by_id(post_id)
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "POST_NOT_FOUND", "message": "게시글을 찾을 수 없습니다."},
            )
        return post

    async def _get_user_name(self, user_id: str | None) -> str | None:
        if not user_id:
            return None
        result = await self.db.scalar(select(User.name).where(User.id == user_id))
        return str(result) if result is not None else None

    def _check_read_permission(self, board: Board, payload: dict[str, Any]) -> None:
        is_logged_in = bool(payload.get("sub"))
        if is_logged_in and not board.read_yn:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "BOARD_READ_FORBIDDEN", "message": "읽기 권한이 없습니다."},
            )
        if not is_logged_in and not board.guest_read_yn:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "BOARD_READ_FORBIDDEN", "message": "읽기 권한이 없습니다."},
            )

    async def _validate_files(
        self, file_ids: list[str], board: Board, user_id: str, user_level: int
    ) -> list[File]:
        if not file_ids:
            return []
        if not board.attach_yn:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "ATTACH_NOT_ALLOWED",
                    "message": "첨부파일이 허용되지 않는 게시판입니다.",
                },
            )
        if len(file_ids) > board.attach_count:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "ATTACH_COUNT_EXCEEDED",
                    "message": f"첨부 파일은 최대 {board.attach_count}개입니다.",
                },
            )

        allowed_exts = (
            [e.strip().lower() for e in board.attach_ext.split(",")] if board.attach_ext else []
        )
        file_map = {f.id: f for f in await self.file_repo.get_by_ids(file_ids)}
        files: list[File] = []
        for fid in file_ids:
            file = file_map.get(fid)
            if not file:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={"code": "FILE_NOT_FOUND", "message": f"파일을 찾을 수 없습니다: {fid}"},
                )
            if file.created_by != user_id and user_level < 70:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "code": "FILE_ACCESS_FORBIDDEN",
                        "message": "파일 접근 권한이 없습니다.",
                    },
                )
            if file.file_size > board.attach_size * 1024:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "code": "ATTACH_SIZE_EXCEEDED",
                        "message": "파일 크기가 허용 한도를 초과했습니다.",
                    },
                )
            if allowed_exts and file.file_ext.lower() not in allowed_exts:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "code": "ATTACH_EXT_NOT_ALLOWED",
                        "message": "허용되지 않는 파일 확장자입니다.",
                    },
                )
            files.append(file)
        return files

    async def _build_file_responses(self, file_maps: list[FileMap]) -> list[FileResponse]:
        if not file_maps:
            return []
        file_ids = [fm.file_id for fm in file_maps]
        files = await self.file_repo.get_by_ids(file_ids)
        return [
            FileResponse(
                file_id=f.id,
                original_name=f.original_name,
                url_path=f.url_path,
                file_size=f.file_size,
                file_ext=f.file_ext,
            )
            for f in files
        ]
