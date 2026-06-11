import { useState } from "react";

import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight } from "lucide-react";

import { useAdminBoards } from "~/features/boards/hooks/useAdminBoards";
import { usePostDetail } from "~/features/posts/hooks/usePostDetail";
import { useDeletePost, useRestorePost } from "~/features/posts/hooks/usePostMutations";
import { usePosts } from "~/features/posts/hooks/usePosts";
import { PostDetailDialog } from "~/features/posts/ui/PostDetailDialog";
import { PostFilterBar } from "~/features/posts/ui/PostFilterBar";
import { PostTable } from "~/features/posts/ui/PostTable";

import { ApiError } from "~/shared/api/client";
import { openModal } from "~/shared/stores/modalStore";
import { Button } from "~/shared/ui/button";

import type { AdminPostDeletedStatus, AdminPostListItem } from "~/entities/post/types";
import type { NoticeFilter } from "~/features/posts/ui/PostFilterBar";

function getPageNumbers(currentPage: number, totalPages: number) {
  const groupStart = Math.floor((currentPage - 1) / 10) * 10 + 1;
  const groupEnd = Math.min(totalPages, groupStart + 9);

  return Array.from({ length: groupEnd - groupStart + 1 }, (_, index) => groupStart + index);
}

export function PostsPage() {
  const [keyword, setKeyword] = useState("");
  const [boardId, setBoardId] = useState("");
  const [authorKeyword, setAuthorKeyword] = useState("");
  const [noticeYn, setNoticeYn] = useState<NoticeFilter>("all");
  const [deletedStatus, setDeletedStatus] = useState<AdminPostDeletedStatus>("active");
  const [page, setPage] = useState(1);
  const [detailPostId, setDetailPostId] = useState<string | null>(null);

  const boardsQuery = useAdminBoards({ keyword: "", useYn: "all", page: 1, size: 100 });
  const postsQuery = usePosts({
    keyword,
    boardId,
    authorKeyword,
    noticeYn,
    deletedStatus,
    page,
  });
  const detailQuery = usePostDetail(detailPostId);
  const deletePost = useDeletePost();
  const restorePost = useRestorePost();

  const data = postsQuery.data;
  const totalPages = data ? Math.max(1, Math.ceil(data.total / data.size)) : 1;
  const pageNumbers = getPageNumbers(page, totalPages);
  const isPending = deletePost.isPending || restorePost.isPending;

  function resetPage() {
    setPage(1);
  }

  function handleDelete(post: AdminPostListItem) {
    openModal({
      type: "confirm",
      title: "게시글 삭제",
      message:
        "물리 삭제가 아니라 논리 삭제로 처리됩니다.\n기본 목록과 사용자 화면에서 제외됩니다.\n댓글과 첨부파일은 삭제하지 않습니다.",
      buttons: [
        { label: "취소", variant: "outline" },
        {
          label: "삭제",
          variant: "destructive",
          onClick: () => {
            deletePost.mutate(post.id, {
              onSuccess: () => {
                if (detailPostId === post.id) {
                  setDetailPostId(null);
                }
                openModal({ type: "alert", message: "게시글이 삭제되었습니다." });
              },
              onError: (error) => {
                openModal({
                  type: "error",
                  message:
                    error instanceof ApiError ? error.message : "게시글을 삭제하지 못했습니다.",
                });
              },
            });
          },
        },
      ],
    });
  }

  function handleRestore(post: AdminPostListItem) {
    openModal({
      type: "confirm",
      title: "게시글 복구",
      message:
        "게시글이 다시 기본 목록과 사용자 화면에 노출될 수 있습니다.\n기존 댓글과 첨부파일은 그대로 유지됩니다.",
      buttons: [
        { label: "취소", variant: "outline" },
        {
          label: "복구",
          onClick: () => {
            restorePost.mutate(post.id, {
              onSuccess: () => {
                if (detailPostId === post.id) {
                  setDetailPostId(null);
                }
                openModal({ type: "alert", message: "게시글이 복구되었습니다." });
              },
              onError: (error) => {
                openModal({
                  type: "error",
                  message:
                    error instanceof ApiError ? error.message : "게시글을 복구하지 못했습니다.",
                });
              },
            });
          },
        },
      ],
    });
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-medium tracking-normal">게시글 관리</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          게시글을 조회하고 논리 삭제 또는 복구를 수행합니다.
        </p>
      </div>

      <PostFilterBar
        keyword={keyword}
        boardId={boardId}
        authorKeyword={authorKeyword}
        noticeYn={noticeYn}
        deletedStatus={deletedStatus}
        boards={boardsQuery.data?.items ?? []}
        onKeywordChange={(value) => {
          setKeyword(value);
          resetPage();
        }}
        onBoardIdChange={(value) => {
          setBoardId(value);
          resetPage();
        }}
        onAuthorKeywordChange={(value) => {
          setAuthorKeyword(value);
          resetPage();
        }}
        onNoticeYnChange={(value) => {
          setNoticeYn(value);
          resetPage();
        }}
        onDeletedStatusChange={(value) => {
          setDeletedStatus(value);
          resetPage();
        }}
      />

      <PostTable
        posts={data?.items ?? []}
        isLoading={postsQuery.isLoading}
        isError={postsQuery.isError}
        isPending={isPending}
        rowNumberStart={(data?.total ?? 0) - (page - 1) * (data?.size ?? 10)}
        onRetry={() => void postsQuery.refetch()}
        onDetail={(postId) => setDetailPostId(postId)}
        onDelete={handleDelete}
        onRestore={handleRestore}
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

      <PostDetailDialog
        post={detailQuery.data}
        open={detailPostId !== null}
        isLoading={detailQuery.isLoading}
        isError={detailQuery.isError}
        isPending={isPending}
        onRetry={() => void detailQuery.refetch()}
        onClose={() => setDetailPostId(null)}
        onDelete={handleDelete}
        onRestore={handleRestore}
      />
    </div>
  );
}
