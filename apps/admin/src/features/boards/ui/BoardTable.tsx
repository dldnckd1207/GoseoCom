import { Pencil, RefreshCcw, Tags, Trash2 } from "lucide-react";

import { Button } from "~/shared/ui/button";

import type { AdminBoard } from "~/entities/board/types";

interface BoardTableProps {
  boards: AdminBoard[];
  isLoading: boolean;
  isError: boolean;
  rowNumberStart: number;
  onRetry: () => void;
  onEdit: (board: AdminBoard) => void;
  onManageCategories: (board: AdminBoard) => void;
  onDelete: (boardId: string) => void;
  isDeleting: boolean;
}

export function BoardTable({
  boards,
  isLoading,
  isError,
  rowNumberStart,
  onRetry,
  onEdit,
  onManageCategories,
  onDelete,
  isDeleting,
}: BoardTableProps) {
  if (isLoading) {
    return <div className="rounded-md border border-border bg-card p-8 text-sm text-muted-foreground">게시판 목록을 불러오는 중입니다.</div>;
  }

  if (isError) {
    return (
      <div className="flex items-center justify-between rounded-md border border-border bg-card p-5">
        <p className="text-sm text-muted-foreground">게시판 목록을 불러오지 못했습니다.</p>
        <Button variant="outline" onClick={onRetry}>
          <RefreshCcw />
          다시 시도
        </Button>
      </div>
    );
  }

  if (boards.length === 0) {
    return <div className="rounded-md border border-border bg-card p-8 text-sm text-muted-foreground">조건에 맞는 게시판이 없습니다.</div>;
  }

  return (
    <div className="overflow-hidden rounded-md border border-border bg-card">
      <table className="w-full min-w-[860px] text-left text-sm">
        <thead className="border-b border-border bg-muted/60 text-xs uppercase tracking-[0.08em] text-muted-foreground">
          <tr>
            <th className="w-16 px-4 py-3 font-medium">순번</th>
            <th className="px-4 py-3 font-medium">게시판코드</th>
            <th className="px-4 py-3 font-medium">게시판명</th>
            <th className="px-4 py-3 font-medium">그룹</th>
            <th className="px-4 py-3 font-medium">타입</th>
            <th className="px-4 py-3 font-medium">권한</th>
            <th className="px-4 py-3 font-medium">상태</th>
            <th className="w-40 px-4 py-3 font-medium">관리</th>
          </tr>
        </thead>
        <tbody>
          {boards.map((board, index) => (
            <tr key={board.id} className="border-b border-border last:border-b-0">
              <td className="px-4 py-3 text-muted-foreground tabular-nums">
                {rowNumberStart - index}
              </td>
              <td className="px-4 py-3 font-mono text-xs">{board.board_code}</td>
              <td className="px-4 py-3">
                <div className="font-medium">{board.board_name}</div>
              </td>
              <td className="px-4 py-3">{board.board_group ?? "-"}</td>
              <td className="px-4 py-3">{board.board_type}</td>
              <td className="px-4 py-3 text-xs text-muted-foreground">
                읽기 {board.guest_read_yn ? "공개" : "회원"} · 쓰기 {board.write_yn ? "허용" : "차단"}
              </td>
              <td className="px-4 py-3">
                <span className="rounded-full border border-border px-2 py-1 text-xs">
                  {board.use_yn ? "사용" : "미사용"}
                </span>
              </td>
              <td className="px-4 py-3">
                <Button
                  aria-label="게시판 수정"
                  variant="ghost"
                  size="icon"
                  onClick={() => onEdit(board)}
                >
                  <Pencil />
                </Button>
                <Button
                  aria-label="카테고리 관리"
                  title={board.category_yn ? "카테고리 관리" : "게시판 수정에서 카테고리 사용을 켜주세요."}
                  variant="ghost"
                  size="icon"
                  disabled={!board.category_yn}
                  onClick={() => onManageCategories(board)}
                >
                  <Tags />
                </Button>
                <Button
                  aria-label="게시판 삭제"
                  variant="ghost"
                  size="icon"
                  disabled={isDeleting}
                  onClick={() => onDelete(board.id)}
                >
                  <Trash2 />
                </Button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
