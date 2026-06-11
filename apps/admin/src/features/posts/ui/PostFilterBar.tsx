import { Search } from "lucide-react";

import type { AdminBoard } from "~/entities/board/types";
import type { AdminPostDeletedStatus } from "~/entities/post/types";

export type NoticeFilter = "all" | "notice" | "normal";

interface PostFilterBarProps {
  keyword: string;
  boardId: string;
  authorKeyword: string;
  noticeYn: NoticeFilter;
  deletedStatus: AdminPostDeletedStatus;
  boards: AdminBoard[];
  onKeywordChange: (value: string) => void;
  onBoardIdChange: (value: string) => void;
  onAuthorKeywordChange: (value: string) => void;
  onNoticeYnChange: (value: NoticeFilter) => void;
  onDeletedStatusChange: (value: AdminPostDeletedStatus) => void;
}

export function PostFilterBar({
  keyword,
  boardId,
  authorKeyword,
  noticeYn,
  deletedStatus,
  boards,
  onKeywordChange,
  onBoardIdChange,
  onAuthorKeywordChange,
  onNoticeYnChange,
  onDeletedStatusChange,
}: PostFilterBarProps) {
  return (
    <section className="grid gap-3 rounded-md border border-border bg-card p-4 md:grid-cols-[1fr_180px_180px_150px_150px]">
      <label className="relative">
        <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
        <input
          value={keyword}
          onChange={(event) => onKeywordChange(event.target.value)}
          className="h-10 w-full rounded-md border border-border bg-secondary pl-9 pr-3 text-sm outline-none focus:ring-3 focus:ring-ring/30"
          placeholder="제목 또는 본문 검색"
        />
      </label>
      <select
        value={boardId}
        onChange={(event) => onBoardIdChange(event.target.value)}
        className="h-10 rounded-md border border-border bg-secondary px-3 text-sm outline-none focus:ring-3 focus:ring-ring/30"
      >
        <option value="">전체 게시판</option>
        {boards.map((board) => (
          <option key={board.id} value={board.id}>
            {board.board_name}
          </option>
        ))}
      </select>
      <input
        value={authorKeyword}
        onChange={(event) => onAuthorKeywordChange(event.target.value)}
        className="h-10 rounded-md border border-border bg-secondary px-3 text-sm outline-none focus:ring-3 focus:ring-ring/30"
        placeholder="작성자 또는 ID"
      />
      <select
        value={noticeYn}
        onChange={(event) => onNoticeYnChange(event.target.value as NoticeFilter)}
        className="h-10 rounded-md border border-border bg-secondary px-3 text-sm outline-none focus:ring-3 focus:ring-ring/30"
      >
        <option value="all">전체 공지</option>
        <option value="notice">공지</option>
        <option value="normal">일반</option>
      </select>
      <select
        value={deletedStatus}
        onChange={(event) => onDeletedStatusChange(event.target.value as AdminPostDeletedStatus)}
        className="h-10 rounded-md border border-border bg-secondary px-3 text-sm outline-none focus:ring-3 focus:ring-ring/30"
      >
        <option value="active">정상</option>
        <option value="deleted">삭제됨</option>
        <option value="all">전체</option>
      </select>
    </section>
  );
}
