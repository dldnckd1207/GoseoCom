"""게시판 Service — 비즈니스 로직"""

from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.board.models import Board, BoardCategory
from app.board.repository import BoardRepository
from app.board.schemas import (
    AdminBoardCategoryCreateRequest,
    AdminBoardCategoryResponse,
    AdminBoardCategoryUpdateRequest,
    AdminBoardCreateRequest,
    AdminBoardListRequest,
    AdminBoardResponse,
    AdminBoardUpdateRequest,
    BoardCategoryResponse,
    BoardDetailResponse,
    BoardListRequest,
    BoardSummaryResponse,
)
from app.core.common.id_generator import next_id
from app.core.common.response import PageData


class BoardService:
    def __init__(self, db: AsyncSession) -> None:
        self.repo = BoardRepository(db)
        self.db = db

    # ------------------------------------------------------------------
    # 클라이언트 API
    # ------------------------------------------------------------------

    async def list_boards(
        self, req: BoardListRequest, payload: dict[str, Any]
    ) -> PageData[BoardSummaryResponse]:
        is_logged_in = bool(payload.get("sub"))
        if is_logged_in:
            boards, total = await self.repo.list_for_user(req)
        else:
            boards, total = await self.repo.list_for_guest(req)
        return PageData(
            items=[BoardSummaryResponse.model_validate(b) for b in boards],
            total=total,
            page=req.page,
            size=req.size,
        )

    async def get_board_by_code(
        self, board_code: str, payload: dict[str, Any]
    ) -> BoardDetailResponse:
        board = await self.repo.get_by_code(board_code)
        if not board:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "BOARD_NOT_FOUND", "message": "게시판을 찾을 수 없습니다."},
            )
        is_logged_in = bool(payload.get("sub"))
        if not is_logged_in and not board.guest_read_yn:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "FORBIDDEN", "message": "접근 권한이 없습니다."},
            )
        return BoardDetailResponse.model_validate(board)

    async def list_categories(self, board_code: str) -> list[BoardCategoryResponse]:
        categories = await self.repo.get_categories_by_board_code(board_code)
        return [BoardCategoryResponse.model_validate(c) for c in categories]

    # ------------------------------------------------------------------
    # 관리자 API
    # ------------------------------------------------------------------

    async def admin_list_boards(self, req: AdminBoardListRequest) -> PageData[AdminBoardResponse]:
        boards, total = await self.repo.admin_list(req)
        return PageData(
            items=[AdminBoardResponse.model_validate(b) for b in boards],
            total=total,
            page=req.page,
            size=req.size,
        )

    async def admin_get_board(self, board_id: str) -> AdminBoardResponse:
        board = await self.repo.get_by_id(board_id)
        if not board:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "BOARD_NOT_FOUND", "message": "게시판을 찾을 수 없습니다."},
            )
        return AdminBoardResponse.model_validate(board)

    async def admin_create_board(
        self, req: AdminBoardCreateRequest, user_id: str
    ) -> AdminBoardResponse:
        existing = await self.repo.get_by_code_for_admin(req.board_code)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "BOARD_CODE_ALREADY_EXISTS",
                    "message": "이미 사용 중인 게시판 코드입니다.",
                },
            )
        now = datetime.now(UTC)
        board = Board(
            id=await next_id("BRD_", self.db),
            board_code=req.board_code,
            board_name=req.board_name,
            board_desc=req.board_desc,
            board_type=req.board_type,
            read_yn=req.read_yn,
            guest_read_yn=req.guest_read_yn,
            write_yn=req.write_yn,
            guest_write_yn=req.guest_write_yn,
            notice_yn=req.notice_yn,
            reply_yn=req.reply_yn,
            comment_yn=req.comment_yn,
            category_yn=req.category_yn,
            attach_yn=req.attach_yn,
            attach_ext=req.attach_ext,
            attach_size=req.attach_size,
            attach_count=req.attach_count,
            list_count=req.list_count,
            auto_reply_enabled=req.auto_reply_enabled,
            auto_reply_delay_min=req.auto_reply_delay_min,
            sort_order=req.sort_order,
            created_at=now,
            created_by=user_id,
            updated_at=now,
            updated_by=user_id,
        )
        created = await self.repo.create(board)
        await self.db.commit()
        await self.db.refresh(created)
        return AdminBoardResponse.model_validate(created)

    async def admin_update_board(
        self, board_id: str, req: AdminBoardUpdateRequest, user_id: str
    ) -> AdminBoardResponse:
        board = await self.repo.get_by_id(board_id)
        if not board:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "BOARD_NOT_FOUND", "message": "게시판을 찾을 수 없습니다."},
            )
        update_fields = req.model_dump(exclude_none=True)
        for field, value in update_fields.items():
            setattr(board, field, value)
        board.updated_at = datetime.now(UTC)
        board.updated_by = user_id

        updated = await self.repo.update(board)
        await self.db.commit()
        await self.db.refresh(updated)
        return AdminBoardResponse.model_validate(updated)

    async def admin_delete_board(self, board_id: str, user_id: str) -> None:
        board = await self.repo.get_by_id(board_id)
        if not board:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "BOARD_NOT_FOUND", "message": "게시판을 찾을 수 없습니다."},
            )
        await self.repo.soft_delete(board, deleted_by=user_id)
        await self.db.commit()

    async def admin_list_categories(self, board_id: str) -> list[AdminBoardCategoryResponse]:
        board = await self._get_admin_board_or_404(board_id)
        categories = await self.repo.admin_list_categories(board.id)
        return [AdminBoardCategoryResponse.model_validate(c) for c in categories]

    async def admin_create_category(
        self, board_id: str, req: AdminBoardCategoryCreateRequest, user_id: str
    ) -> AdminBoardCategoryResponse:
        board = await self._get_admin_board_or_404(board_id)
        now = datetime.now(UTC)
        category = BoardCategory(
            id=await next_id("BCAT_", self.db),
            board_id=board.id,
            category_name=req.category_name,
            sort_order=req.sort_order,
            use_yn=req.use_yn,
            created_at=now,
            created_by=user_id,
            updated_at=now,
            updated_by=user_id,
        )
        created = await self.repo.create_category(category)
        await self.db.commit()
        await self.db.refresh(created)
        return AdminBoardCategoryResponse.model_validate(created)

    async def admin_update_category(
        self,
        board_id: str,
        category_id: str,
        req: AdminBoardCategoryUpdateRequest,
        user_id: str,
    ) -> AdminBoardCategoryResponse:
        await self._get_admin_board_or_404(board_id)
        category = await self.repo.admin_get_category(board_id, category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "CATEGORY_NOT_FOUND", "message": "카테고리를 찾을 수 없습니다."},
            )
        update_fields = req.model_dump(exclude_none=True)
        for field, value in update_fields.items():
            setattr(category, field, value)
        category.updated_at = datetime.now(UTC)
        category.updated_by = user_id

        updated = await self.repo.update_category(category)
        await self.db.commit()
        await self.db.refresh(updated)
        return AdminBoardCategoryResponse.model_validate(updated)

    async def admin_delete_category(self, board_id: str, category_id: str, user_id: str) -> None:
        await self._get_admin_board_or_404(board_id)
        category = await self.repo.admin_get_category(board_id, category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "CATEGORY_NOT_FOUND", "message": "카테고리를 찾을 수 없습니다."},
            )
        await self.repo.soft_delete_category(category, deleted_by=user_id)
        await self.db.commit()

    async def _get_admin_board_or_404(self, board_id: str) -> Board:
        board = await self.repo.get_by_id(board_id)
        if not board:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "BOARD_NOT_FOUND", "message": "게시판을 찾을 수 없습니다."},
            )
        return board
