import { useState } from "react";

import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight, Search } from "lucide-react";

import { useApproveComment, useRejectComment } from "~/features/comments/hooks/useCommentReview";
import { useFilteredComments } from "~/features/comments/hooks/useFilteredComments";
import { FilteredCommentTable } from "~/features/comments/ui/FilteredCommentTable";

import { Button } from "~/shared/ui/button";

function getPageNumbers(currentPage: number, totalPages: number) {
  const groupStart = Math.floor((currentPage - 1) / 10) * 10 + 1;
  const groupEnd = Math.min(totalPages, groupStart + 9);
  return Array.from({ length: groupEnd - groupStart + 1 }, (_, i) => groupStart + i);
}

export function FilteredCommentsPage() {
  const [keyword, setKeyword] = useState("");
  const [inputValue, setInputValue] = useState("");
  const [page, setPage] = useState(1);

  const { data, isLoading, isError, refetch } = useFilteredComments({ keyword, page });
  const approve = useApproveComment();
  const reject = useRejectComment();

  const isPending = approve.isPending || reject.isPending;
  const totalPages = data ? Math.max(1, Math.ceil(data.total / 20)) : 1;
  const pageNumbers = getPageNumbers(page, totalPages);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setKeyword(inputValue);
    setPage(1);
  };

  const handleApprove = (commentId: string) => {
    if (!confirm("이 댓글을 공개하시겠습니까? 필터링이 해제되어 정상 댓글로 표시됩니다.")) return;
    approve.mutate(commentId);
  };

  const handleReject = (commentId: string) => {
    if (!confirm("이 댓글을 삭제하시겠습니까? 복구할 수 없습니다.")) return;
    reject.mutate(commentId);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">댓글 필터링</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          AI가 악성으로 감지한 댓글을 검토하고 승인 또는 삭제합니다.
        </p>
      </div>

      <form onSubmit={handleSearch} className="flex items-center gap-2">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="댓글 내용 또는 작성자 검색..."
            className="w-full rounded-md border border-input bg-background pl-9 pr-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
          />
        </div>
        <Button type="submit" variant="outline" size="sm">
          검색
        </Button>
      </form>

      <div className="text-sm text-muted-foreground">
        전체 <span className="font-medium text-foreground">{data?.total ?? 0}</span>건
      </div>

      <FilteredCommentTable
        comments={data?.items ?? []}
        isLoading={isLoading}
        isError={isError}
        onRetry={() => void refetch()}
        onApprove={handleApprove}
        onReject={handleReject}
        isPending={isPending}
      />

      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-1">
          <Button
            variant="outline"
            size="sm"
            disabled={page === 1}
            onClick={() => setPage(1)}
          >
            <ChevronsLeft className="size-4" />
          </Button>
          <Button
            variant="outline"
            size="sm"
            disabled={page === 1}
            onClick={() => setPage((p) => p - 1)}
          >
            <ChevronLeft className="size-4" />
          </Button>
          {pageNumbers.map((n) => (
            <Button
              key={n}
              variant={n === page ? "default" : "outline"}
              size="sm"
              onClick={() => setPage(n)}
            >
              {n}
            </Button>
          ))}
          <Button
            variant="outline"
            size="sm"
            disabled={page === totalPages}
            onClick={() => setPage((p) => p + 1)}
          >
            <ChevronRight className="size-4" />
          </Button>
          <Button
            variant="outline"
            size="sm"
            disabled={page === totalPages}
            onClick={() => setPage(totalPages)}
          >
            <ChevronsRight className="size-4" />
          </Button>
        </div>
      )}
    </div>
  );
}
