"""댓글 Service — 비즈니스 로직"""

from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.board.comment_repository import CommentRepository
from app.board.comment_schemas import (
    AdminCommentListRequest,
    AdminCommentResponse,
    CommentCreateRequest,
    CommentListRequest,
    CommentResponse,
    CommentUpdateRequest,
)
from app.board.models import Comment
from app.board.post_repository import PostRepository
from app.board.repository import BoardRepository
from app.config import settings
from app.core.common.id_generator import next_id
from app.core.common.response import PageData

_PLACEHOLDER_CONTENT = "삭제된 댓글입니다."


def _is_ai_gen(user_id: str) -> bool:
    return user_id == settings.ai_agent_user_id


def _to_response(comment: Comment, replies: list[CommentResponse] | None = None) -> CommentResponse:
    is_deleted = comment.del_yn
    return CommentResponse(
        id=comment.id,
        post_id=comment.post_id,
        user_id=None if is_deleted else comment.user_id,
        author_name=None if is_deleted else comment.author_name,
        is_ai_gen=_is_ai_gen(comment.user_id),
        is_deleted=is_deleted,
        is_filtered=comment.is_filtered,
        filter_reason=comment.filter_reason,
        parent_id=comment.parent_id,
        depth=comment.depth,
        content=_PLACEHOLDER_CONTENT if is_deleted else comment.content,
        created_at=comment.created_at,
        updated_at=comment.updated_at,
        replies=replies or [],
    )


class CommentService:
    def __init__(self, db: AsyncSession) -> None:
        self.comment_repo = CommentRepository(db)
        self.post_repo = PostRepository(db)
        self.board_repo = BoardRepository(db)
        self.db = db

    async def list_comments(
        self, post_id: str, req: CommentListRequest, payload: dict[str, Any]
    ) -> PageData[CommentResponse]:
        post = await self.post_repo.get_by_id(post_id)
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "POST_NOT_FOUND", "message": "게시글을 찾을 수 없습니다."},
            )
        board = await self.board_repo.get_by_id(post.board_id)
        if not board:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "BOARD_NOT_FOUND", "message": "게시판을 찾을 수 없습니다."},
            )

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

        roots, total = await self.comment_repo.list_roots(post_id, req.page, req.size)
        root_ids = [r.id for r in roots]
        replies_all = await self.comment_repo.list_replies_by_roots(root_ids)

        replies_map: dict[str, list[CommentResponse]] = {rid: [] for rid in root_ids}
        for reply in replies_all:
            if reply.parent_id in replies_map:
                replies_map[reply.parent_id].append(_to_response(reply))

        items = [_to_response(r, replies_map.get(r.id, [])) for r in roots]
        return PageData(items=items, total=total, page=req.page, size=req.size)

    async def create_comment(
        self, post_id: str, req: CommentCreateRequest, payload: dict[str, Any]
    ) -> CommentResponse:
        user_id: str = payload["sub"]
        author_name: str = payload.get("name", "")

        post = await self.post_repo.get_by_id(post_id)
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "POST_NOT_FOUND", "message": "게시글을 찾을 수 없습니다."},
            )
        board = await self.board_repo.get_by_id(post.board_id)
        if not board or not board.use_yn:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "BOARD_NOT_FOUND", "message": "게시판을 찾을 수 없습니다."},
            )
        if not board.comment_yn:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "COMMENT_NOT_ALLOWED",
                    "message": "댓글이 허용되지 않는 게시판입니다.",
                },
            )

        depth = 0
        if req.parent_id:
            parent = await self.comment_repo.get_by_id(req.parent_id)
            if not parent or parent.post_id != post_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "code": "REPLY_NOT_ALLOWED",
                        "message": "대댓글 대상을 찾을 수 없습니다.",
                    },
                )
            if parent.depth != 0:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "code": "REPLY_NOT_ALLOWED",
                        "message": "대댓글의 대댓글은 허용되지 않습니다.",
                    },
                )
            depth = 1

        now = datetime.now(UTC)
        comment = Comment(
            id=await next_id("CMT_", self.db),
            post_id=post_id,
            user_id=user_id,
            author_name=author_name,
            parent_id=req.parent_id,
            depth=depth,
            content=req.content,
            filter_status="PENDING",
            created_at=now,
            created_by=user_id,
            updated_at=now,
            updated_by=user_id,
        )
        created = await self.comment_repo.create(comment)
        await self.post_repo.increment_comment_count(post_id)
        await self.db.commit()
        await self.db.refresh(created)
        return _to_response(created)

    async def update_comment(
        self,
        post_id: str,
        comment_id: str,
        req: CommentUpdateRequest,
        payload: dict[str, Any],
    ) -> CommentResponse:
        user_id: str = payload["sub"]
        user_level: int = payload["level"]

        comment = await self.comment_repo.get_by_id_and_post(comment_id, post_id)
        if not comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "COMMENT_NOT_FOUND", "message": "댓글을 찾을 수 없습니다."},
            )
        if comment.user_id != user_id and user_level < 70:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "FORBIDDEN", "message": "수정 권한이 없습니다."},
            )

        now = datetime.now(UTC)
        comment.content = req.content
        comment.updated_at = now
        comment.updated_by = user_id

        await self.db.commit()
        await self.db.refresh(comment)
        return _to_response(comment)

    async def delete_comment(self, post_id: str, comment_id: str, payload: dict[str, Any]) -> None:
        user_id: str = payload["sub"]
        user_level: int = payload["level"]

        comment = await self.comment_repo.get_by_id_and_post(comment_id, post_id)
        if not comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "COMMENT_NOT_FOUND", "message": "댓글을 찾을 수 없습니다."},
            )
        if comment.user_id != user_id and user_level < 70:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "FORBIDDEN", "message": "삭제 권한이 없습니다."},
            )

        await self.comment_repo.soft_delete(comment, deleted_by=user_id)
        await self.post_repo.decrement_comment_count(post_id)
        await self.db.commit()

    # ── 관리자 ──────────────────────────────────────────────────────────────

    async def admin_list_flagged(
        self, req: AdminCommentListRequest
    ) -> PageData[AdminCommentResponse]:
        comments, total = await self.comment_repo.list_flagged_admin(
            req.keyword, req.page, req.size
        )
        items: list[AdminCommentResponse] = []
        for comment in comments:
            post = await self.post_repo.get_by_id(comment.post_id)
            board = await self.board_repo.get_by_id(post.board_id) if post else None
            items.append(
                AdminCommentResponse(
                    id=comment.id,
                    post_id=comment.post_id,
                    post_title=post.title if post else "",
                    board_name=board.board_name if board else "",
                    user_id=comment.user_id,
                    author_name=comment.author_name,
                    content=comment.content,
                    filter_reason=comment.filter_reason,
                    filtered_at=comment.filtered_at,
                    filter_reviewed_by=comment.filter_reviewed_by,
                    created_at=comment.created_at,
                )
            )
        return PageData(items=items, total=total, page=req.page, size=req.size)

    async def admin_approve_comment(
        self, comment_id: str, reviewer_id: str
    ) -> AdminCommentResponse:
        comment = await self.comment_repo.get_by_id(comment_id)
        if not comment or comment.filter_status != "FLAGGED":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "COMMENT_NOT_FOUND",
                    "message": "필터링된 댓글을 찾을 수 없습니다.",
                },
            )

        now = datetime.now(UTC)
        comment.is_filtered = False
        comment.filter_status = "CLEAN"
        comment.filter_reviewed_by = reviewer_id
        comment.updated_at = now
        comment.updated_by = reviewer_id

        await self.db.commit()
        await self.db.refresh(comment)

        post = await self.post_repo.get_by_id(comment.post_id)
        board = await self.board_repo.get_by_id(post.board_id) if post else None
        return AdminCommentResponse(
            id=comment.id,
            post_id=comment.post_id,
            post_title=post.title if post else "",
            board_name=board.board_name if board else "",
            user_id=comment.user_id,
            author_name=comment.author_name,
            content=comment.content,
            filter_reason=comment.filter_reason,
            filtered_at=comment.filtered_at,
            filter_reviewed_by=comment.filter_reviewed_by,
            created_at=comment.created_at,
        )

    async def admin_reject_comment(self, comment_id: str, reviewer_id: str) -> None:
        comment = await self.comment_repo.get_by_id(comment_id)
        if not comment or comment.filter_status != "FLAGGED":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "COMMENT_NOT_FOUND",
                    "message": "필터링된 댓글을 찾을 수 없습니다.",
                },
            )

        comment.filter_reviewed_by = reviewer_id
        await self.comment_repo.soft_delete(comment, deleted_by=reviewer_id)
        await self.post_repo.decrement_comment_count(comment.post_id)
        await self.db.commit()
