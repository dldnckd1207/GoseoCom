import { RefreshCcw } from "lucide-react";

import { Button } from "~/shared/ui/button";

import type { AdminCommentItem } from "~/features/comments/types";

interface Props {
  comments: AdminCommentItem[];
  isLoading: boolean;
  isError: boolean;
  onRetry: () => void;
  onApprove: (commentId: string) => void;
  onReject: (commentId: string) => void;
  isPending: boolean;
}

export function FilteredCommentTable({
  comments,
  isLoading,
  isError,
  onRetry,
  onApprove,
  onReject,
  isPending,
}: Props) {
  if (isLoading) {
    return (
      <div className="rounded-md border border-border bg-card p-8 text-sm text-muted-foreground">
        필터링된 댓글을 불러오는 중입니다.
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex items-center justify-between rounded-md border border-border bg-card p-5">
        <p className="text-sm text-muted-foreground">목록을 불러오지 못했습니다.</p>
        <Button variant="outline" onClick={onRetry}>
          <RefreshCcw className="mr-1 size-4" />
          다시 시도
        </Button>
      </div>
    );
  }

  if (comments.length === 0) {
    return (
      <div className="rounded-md border border-border bg-card p-8 text-sm text-muted-foreground">
        필터링된 댓글이 없습니다.
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-md border border-border bg-card">
      <table className="w-full min-w-[900px] text-left text-sm">
        <thead>
          <tr className="border-b border-border bg-muted/40">
            <th className="px-4 py-3 font-medium text-muted-foreground">작성자</th>
            <th className="px-4 py-3 font-medium text-muted-foreground">댓글 내용</th>
            <th className="px-4 py-3 font-medium text-muted-foreground">게시글</th>
            <th className="px-4 py-3 font-medium text-muted-foreground">필터 사유</th>
            <th className="px-4 py-3 font-medium text-muted-foreground">작성 시각</th>
            <th className="px-4 py-3 font-medium text-muted-foreground">작업</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {comments.map((comment) => (
            <tr key={comment.id} className="hover:bg-muted/20 transition-colors">
              <td className="px-4 py-3 text-foreground">{comment.author_name}</td>
              <td className="px-4 py-3 max-w-[240px]">
                <p className="truncate text-foreground" title={comment.content}>
                  {comment.content}
                </p>
              </td>
              <td className="px-4 py-3">
                <p className="truncate max-w-[160px] text-muted-foreground" title={comment.post_title}>
                  {comment.post_title}
                </p>
                <p className="text-xs text-muted-foreground/60">{comment.board_name}</p>
              </td>
              <td className="px-4 py-3 max-w-[180px]">
                <p className="truncate text-muted-foreground text-xs" title={comment.filter_reason ?? ""}>
                  {comment.filter_reason ?? "-"}
                </p>
              </td>
              <td className="px-4 py-3 text-muted-foreground whitespace-nowrap">
                {comment.created_at ? new Date(comment.created_at).toLocaleString("ko-KR") : "-"}
              </td>
              <td className="px-4 py-3">
                <div className="flex items-center gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    className="border-green-500 text-green-600 hover:bg-green-50 dark:hover:bg-green-950"
                    disabled={isPending}
                    onClick={() => onApprove(comment.id)}
                  >
                    공개
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    className="border-red-400 text-red-500 hover:bg-red-50 dark:hover:bg-red-950"
                    disabled={isPending}
                    onClick={() => onReject(comment.id)}
                  >
                    삭제
                  </Button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
