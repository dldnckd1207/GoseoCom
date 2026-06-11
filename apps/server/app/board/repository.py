"""게시판 Repository — DB 쿼리"""

from datetime import UTC, datetime

from sqlalchemy import ColumnElement, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.board.models import Board, BoardCategory, Comment, Post
from app.board.schemas import AdminBoardListRequest, BoardListRequest


class BoardRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # 클라이언트 API
    # ------------------------------------------------------------------

    async def list_for_guest(self, req: BoardListRequest) -> tuple[list[Board], int]:
        """비회원 게시판 목록.
        board_group 지정 시 그룹 내 전체 게시판 노출 (guest_read_yn 무관).
        미지정 시 guest_read_yn=true 필터 적용.
        """
        conditions: list[ColumnElement[bool]] = [Board.use_yn.is_(True), Board.del_yn.is_(False)]
        if req.board_group is not None:
            conditions.append(Board.board_group == req.board_group)
        else:
            conditions.append(Board.guest_read_yn.is_(True))
        base = select(Board).where(*conditions).order_by(Board.sort_order.asc(), Board.id.desc())
        total_result = await self.db.execute(select(func.count()).select_from(base.subquery()))
        total: int = total_result.scalar_one()
        result = await self.db.execute(base.offset((req.page - 1) * req.size).limit(req.size))
        return list(result.scalars().all()), total

    async def list_for_user(self, req: BoardListRequest) -> tuple[list[Board], int]:
        """로그인 사용자 게시판 목록.
        board_group 지정 시 그룹 내 전체 게시판 노출 (read_yn 무관).
        미지정 시 read_yn=true 필터 적용.
        """
        conditions: list[ColumnElement[bool]] = [Board.use_yn.is_(True), Board.del_yn.is_(False)]
        if req.board_group is not None:
            conditions.append(Board.board_group == req.board_group)
        else:
            conditions.append(Board.read_yn.is_(True))
        base = select(Board).where(*conditions).order_by(Board.sort_order.asc(), Board.id.desc())
        total_result = await self.db.execute(select(func.count()).select_from(base.subquery()))
        total: int = total_result.scalar_one()
        result = await self.db.execute(base.offset((req.page - 1) * req.size).limit(req.size))
        return list(result.scalars().all()), total

    async def get_by_codes(self, board_codes: list[str]) -> list[Board]:
        """board_code 목록으로 게시판 조회.
        게시글 목록은 board_group 소속 게시판이면 로그인 여부와 무관하게 조회 허용.
        열람 권한(guest_read_yn)은 상세 API(get_post)에서 별도 체크한다.
        """
        result = await self.db.execute(
            select(Board).where(
                Board.board_code.in_(board_codes),
                Board.use_yn.is_(True),
                Board.del_yn.is_(False),
            )
        )
        return list(result.scalars().all())

    async def get_by_code(self, board_code: str) -> Board | None:
        result = await self.db.execute(
            select(Board).where(
                Board.board_code == board_code,
                Board.use_yn.is_(True),
                Board.del_yn.is_(False),
            )
        )
        return result.scalar_one_or_none()

    # ------------------------------------------------------------------
    # 관리자 API
    # ------------------------------------------------------------------

    async def admin_list(self, req: AdminBoardListRequest) -> tuple[list[Board], int]:
        conditions = [Board.del_yn.is_(False)]
        if req.use_yn is not None:
            conditions.append(Board.use_yn.is_(req.use_yn))
        if req.keyword:
            conditions.append(Board.board_name.ilike(f"%{req.keyword}%"))

        base = select(Board).where(*conditions).order_by(Board.id.desc())
        total_result = await self.db.execute(select(func.count()).select_from(base.subquery()))
        total: int = total_result.scalar_one()
        result = await self.db.execute(base.offset((req.page - 1) * req.size).limit(req.size))
        return list(result.scalars().all()), total

    async def get_by_id(self, board_id: str) -> Board | None:
        result = await self.db.execute(
            select(Board).where(Board.id == board_id, Board.del_yn.is_(False))
        )
        return result.scalar_one_or_none()

    async def get_by_code_for_admin(self, board_code: str) -> Board | None:
        result = await self.db.execute(
            select(Board).where(Board.board_code == board_code, Board.del_yn.is_(False))
        )
        return result.scalar_one_or_none()

    async def create(self, board: Board) -> Board:
        self.db.add(board)
        await self.db.flush()
        return board

    async def update(self, board: Board) -> Board:
        await self.db.flush()
        return board

    async def soft_delete(self, board: Board, deleted_by: str) -> None:
        deleted_at = datetime.now(UTC)
        board.del_yn = True
        board.deleted_at = deleted_at
        board.deleted_by = deleted_by
        await self.db.execute(
            update(Comment)
            .where(
                Comment.post_id.in_(
                    select(Post.id).where(Post.board_id == board.id, Post.del_yn.is_(False))
                ),
                Comment.del_yn.is_(False),
            )
            .values(del_yn=True, deleted_at=deleted_at, deleted_by=deleted_by)
        )
        await self.db.execute(
            update(Post)
            .where(Post.board_id == board.id, Post.del_yn.is_(False))
            .values(del_yn=True, deleted_at=deleted_at, deleted_by=deleted_by)
        )
        await self.db.execute(
            update(BoardCategory)
            .where(BoardCategory.board_id == board.id, BoardCategory.del_yn.is_(False))
            .values(del_yn=True, deleted_at=deleted_at, deleted_by=deleted_by)
        )
        await self.db.flush()

    async def has_posts(self, board_id: str) -> bool:
        result = await self.db.execute(
            select(func.count()).where(Post.board_id == board_id, Post.del_yn.is_(False))
        )
        return (result.scalar_one() or 0) > 0

    async def get_categories_by_board_code(self, board_code: str) -> list[BoardCategory]:
        result = await self.db.execute(
            select(BoardCategory)
            .join(Board, BoardCategory.board_id == Board.id)
            .where(
                Board.board_code == board_code,
                Board.use_yn.is_(True),
                Board.del_yn.is_(False),
                Board.category_yn.is_(True),
                BoardCategory.use_yn.is_(True),
                BoardCategory.del_yn.is_(False),
            )
            .order_by(BoardCategory.sort_order.asc(), BoardCategory.id.desc())
        )
        return list(result.scalars().all())

    async def get_category_by_id(self, category_id: str) -> BoardCategory | None:
        result = await self.db.execute(
            select(BoardCategory).where(
                BoardCategory.id == category_id,
                BoardCategory.use_yn.is_(True),
                BoardCategory.del_yn.is_(False),
            )
        )
        return result.scalar_one_or_none()

    async def admin_list_categories(self, board_id: str) -> list[BoardCategory]:
        result = await self.db.execute(
            select(BoardCategory)
            .where(BoardCategory.board_id == board_id, BoardCategory.del_yn.is_(False))
            .order_by(BoardCategory.sort_order.asc(), BoardCategory.id.desc())
        )
        return list(result.scalars().all())

    async def admin_get_category(self, board_id: str, category_id: str) -> BoardCategory | None:
        result = await self.db.execute(
            select(BoardCategory).where(
                BoardCategory.id == category_id,
                BoardCategory.board_id == board_id,
                BoardCategory.del_yn.is_(False),
            )
        )
        return result.scalar_one_or_none()

    async def create_category(self, category: BoardCategory) -> BoardCategory:
        self.db.add(category)
        await self.db.flush()
        return category

    async def update_category(self, category: BoardCategory) -> BoardCategory:
        await self.db.flush()
        return category

    async def soft_delete_category(self, category: BoardCategory, deleted_by: str) -> None:
        category.del_yn = True
        category.deleted_at = datetime.now(UTC)
        category.deleted_by = deleted_by
        await self.db.flush()
