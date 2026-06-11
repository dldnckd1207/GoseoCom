import { useState } from "react";

import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight, Search } from "lucide-react";

import { boardApi } from "~/features/boards/api/boardApi";
import { useAdminBoards } from "~/features/boards/hooks/useAdminBoards";
import { useCreateBoard, useUpdateBoard } from "~/features/boards/hooks/useBoardMutations";
import { useDeleteBoard } from "~/features/boards/hooks/useDeleteBoard";
import { formToRequest } from "~/features/boards/lib/boardForm";
import { BoardCategoryDialog } from "~/features/boards/ui/BoardCategoryDialog";
import { BoardFormDialog } from "~/features/boards/ui/BoardFormDialog";
import { BoardTable } from "~/features/boards/ui/BoardTable";

import { openModal } from "~/shared/stores/modalStore";
import { Button } from "~/shared/ui/button";

import type { AdminBoard } from "~/entities/board/types";
import type { BoardFormState } from "~/features/boards/lib/boardForm";

type UseYnFilter = "all" | "active" | "inactive";
type DialogState =
  | { mode: "create"; board: null; open: true }
  | { mode: "edit"; board: AdminBoard; open: true }
  | { mode: "create"; board: null; open: false };
type CategoryDialogState = { board: AdminBoard; open: true } | { board: null; open: false };

function getPageNumbers(currentPage: number, totalPages: number) {
  const groupStart = Math.floor((currentPage - 1) / 10) * 10 + 1;
  const groupEnd = Math.min(totalPages, groupStart + 9);

  return Array.from({ length: groupEnd - groupStart + 1 }, (_, index) => groupStart + index);
}

export function BoardsPage() {
  const [keyword, setKeyword] = useState("");
  const [useYn, setUseYn] = useState<UseYnFilter>("all");
  const [page, setPage] = useState(1);
  const [dialog, setDialog] = useState<DialogState>({ mode: "create", board: null, open: false });
  const [categoryDialog, setCategoryDialog] = useState<CategoryDialogState>({
    board: null,
    open: false,
  });
  const boardsQuery = useAdminBoards({ keyword, useYn, page });
  const deleteBoard = useDeleteBoard();
  const createBoard = useCreateBoard();
  const updateBoard = useUpdateBoard();

  const data = boardsQuery.data;
  const totalPages = data ? Math.max(1, Math.ceil(data.total / data.size)) : 1;
  const pageNumbers = getPageNumbers(page, totalPages);
  const isSaving = createBoard.isPending || updateBoard.isPending;

  function handleDelete(boardId: string) {
    openModal({
      type: "confirm",
      title: "게시판 삭제",
      message: "게시판과 포함된 게시글, 댓글, 카테고리가 모두 삭제됩니다.\n계속 진행할까요?",
      buttons: [
        { label: "취소", variant: "outline" },
        {
          label: "삭제",
          variant: "destructive",
          onClick: () => {
            deleteBoard.mutate(boardId, {
              onError: () => {
                openModal({
                  type: "error",
                  message: "게시판을 삭제하지 못했습니다.",
                });
              },
            });
          },
        },
      ],
    });
  }

  async function handleEdit(board: AdminBoard) {
    try {
      const detail = await boardApi.get(board.id);
      setDialog({ mode: "edit", board: detail, open: true });
    } catch {
      openModal({
        type: "error",
        message: "게시판 상세 정보를 불러오지 못했습니다.",
      });
    }
  }

  function handleSubmit(form: BoardFormState) {
    if (dialog.mode === "create") {
      createBoard.mutate(formToRequest(form, "create"), {
        onSuccess: () => {
          setDialog({ mode: "create", board: null, open: false });
          openModal({ type: "alert", message: "게시판이 등록되었습니다." });
        },
        onError: () => {
          openModal({ type: "error", message: "게시판을 등록하지 못했습니다." });
        },
      });
      return;
    }

    updateBoard.mutate(
      { boardId: dialog.board.id, request: formToRequest(form, "edit") },
      {
        onSuccess: () => {
          setDialog({ mode: "create", board: null, open: false });
          openModal({ type: "alert", message: "게시판이 수정되었습니다." });
        },
        onError: () => {
          openModal({ type: "error", message: "게시판을 수정하지 못했습니다." });
        },
      },
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
        <div>
          <h1 className="text-2xl font-medium tracking-normal">게시판 관리</h1>
          <p className="mt-2 text-sm text-muted-foreground">
            사용/미사용 게시판을 조회하고 논리 삭제를 수행합니다.
          </p>
        </div>
        <Button onClick={() => setDialog({ mode: "create", board: null, open: true })}>
          등록
        </Button>
      </div>

      <section className="flex flex-col gap-3 rounded-md border border-border bg-card p-4 md:flex-row">
        <label className="relative flex-1">
          <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <input
            value={keyword}
            onChange={(event) => {
              setKeyword(event.target.value);
              setPage(1);
            }}
            className="h-10 w-full rounded-md border border-border bg-secondary pl-9 pr-3 text-sm outline-none focus:ring-3 focus:ring-ring/30"
            placeholder="게시판 이름 검색"
          />
        </label>
        <select
          value={useYn}
          onChange={(event) => {
            setUseYn(event.target.value as UseYnFilter);
            setPage(1);
          }}
          className="h-10 rounded-md border border-border bg-secondary px-3 text-sm outline-none focus:ring-3 focus:ring-ring/30"
        >
          <option value="all">전체 사용 여부</option>
          <option value="active">사용</option>
          <option value="inactive">미사용</option>
        </select>
      </section>

      <BoardTable
        boards={data?.items ?? []}
        isLoading={boardsQuery.isLoading}
        isError={boardsQuery.isError}
        rowNumberStart={(data?.total ?? 0) - (page - 1) * (data?.size ?? 10)}
        onRetry={() => void boardsQuery.refetch()}
        onEdit={handleEdit}
        onManageCategories={(board) => setCategoryDialog({ board, open: true })}
        onDelete={handleDelete}
        isDeleting={deleteBoard.isPending}
      />

      <div className="flex flex-col gap-3 text-sm text-muted-foreground md:flex-row md:items-center md:justify-between">
        <span>총 {data?.total ?? 0}개</span>
        <div className="flex flex-wrap items-center gap-1">
          <Button
            variant="outline"
            size="icon"
            className="size-8"
            disabled={page <= 1}
            onClick={() => setPage(1)}
            aria-label="첫 페이지"
          >
            <ChevronsLeft />
          </Button>
          <Button
            variant="outline"
            size="icon"
            className="size-8"
            disabled={page <= 1}
            onClick={() => setPage((current) => Math.max(1, current - 1))}
            aria-label="이전 페이지"
          >
            <ChevronLeft />
          </Button>
          {pageNumbers.map((pageNumber) => (
            <Button
              key={pageNumber}
              variant={pageNumber === page ? "default" : "outline"}
              size="sm"
              className="size-8 px-0 tabular-nums"
              onClick={() => setPage(pageNumber)}
              aria-current={pageNumber === page ? "page" : undefined}
            >
              {pageNumber}
            </Button>
          ))}
          <Button
            variant="outline"
            size="icon"
            className="size-8"
            disabled={page >= totalPages}
            onClick={() => setPage((current) => Math.min(totalPages, current + 1))}
            aria-label="다음 페이지"
          >
            <ChevronRight />
          </Button>
          <Button
            variant="outline"
            size="icon"
            className="size-8"
            disabled={page >= totalPages}
            onClick={() => setPage(totalPages)}
            aria-label="마지막 페이지"
          >
            <ChevronsRight />
          </Button>
        </div>
      </div>

      <BoardFormDialog
        key={`${dialog.mode}-${dialog.board?.id ?? "new"}-${String(dialog.open)}`}
        mode={dialog.mode}
        board={dialog.board}
        open={dialog.open}
        isSaving={isSaving}
        onClose={() => setDialog({ mode: "create", board: null, open: false })}
        onSubmit={handleSubmit}
      />

      <BoardCategoryDialog
        key={`${categoryDialog.board?.id ?? "none"}-${String(categoryDialog.open)}`}
        board={categoryDialog.board}
        open={categoryDialog.open}
        onClose={() => setCategoryDialog({ board: null, open: false })}
      />
    </div>
  );
}
