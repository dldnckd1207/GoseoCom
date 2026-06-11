import { Eye, RefreshCcw, RotateCcw, Trash2 } from "lucide-react";

import { Button } from "~/shared/ui/button";

import type { AdminPostListItem } from "~/entities/post/types";

interface PostTableProps {
  posts: AdminPostListItem[];
  isLoading: boolean;
  isError: boolean;
  isPending: boolean;
  startIndex: number;
  onRetry: () => void;
  onDetail: (postId: string) => void;
  onDelete: (post: AdminPostListItem) => void;
  onRestore: (post: AdminPostListItem) => void;
}

function formatDate(value: string | null) {
  if (!value) return "-";
  return new Intl.DateTimeFormat("ko-KR", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(new Date(value));
}

function Badge({ children }: { children: string }) {
  return <span className="rounded-full border border-border px-2 py-1 text-xs">{children}</span>;
}

export function PostTable({
  posts,
  isLoading,
  isError,
  isPending,
  startIndex,
  onRetry,
  onDetail,
  onDelete,
  onRestore,
}: PostTableProps) {
  if (isLoading) {
    return (
      <div className="rounded-md border border-border bg-card p-8 text-sm text-muted-foreground">
        게시글 목록을 불러오는 중입니다.
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex items-center justify-between rounded-md border border-border bg-card p-5">
        <p className="text-sm text-muted-foreground">게시글 목록을 불러오지 못했습니다.</p>
        <Button variant="outline" onClick={onRetry}>
          <RefreshCcw />
          다시 시도
        </Button>
      </div>
    );
  }

  if (posts.length === 0) {
    return (
      <div className="rounded-md border border-border bg-card p-8 text-sm text-muted-foreground">
        조건에 맞는 게시글이 없습니다.
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-md border border-border bg-card">
      <table className="w-full min-w-[1040px] text-left text-sm">
        <thead className="border-b border-border bg-muted/60 text-xs uppercase tracking-[0.08em] text-muted-foreground">
          <tr>
            <th className="w-16 px-4 py-3 font-medium">순번</th>
            <th className="px-4 py-3 font-medium">게시판</th>
            <th className="px-4 py-3 font-medium">카테고리</th>
            <th className="px-4 py-3 font-medium">게시글</th>
            <th className="px-4 py-3 font-medium">작성자</th>
            <th className="px-4 py-3 font-medium">공지여부</th>
            <th className="px-4 py-3 font-medium">조회수</th>
            <th className="px-4 py-3 font-medium">댓글</th>
            <th className="px-4 py-3 font-medium">작성일</th>
            <th className="px-4 py-3 font-medium">상태</th>
            <th className="w-32 px-4 py-3 font-medium">관리</th>
          </tr>
        </thead>
        <tbody>
          {posts.map((post, index) => (
            <tr key={post.id} className="border-b border-border last:border-b-0">
              <td className="px-4 py-3 text-muted-foreground tabular-nums">
                {startIndex + index + 1}
              </td>
              <td className="px-4 py-3">{post.board_name}</td>
              <td className="px-4 py-3 text-muted-foreground">
                {post.category_name ?? "-"}
              </td>
              <td className="px-4 py-3">
                <div className="max-w-[360px] truncate font-medium" title={post.title}>
                  {post.title}
                </div>
              </td>
              <td className="px-4 py-3">{post.author_name}</td>
              <td className="px-4 py-3">{post.notice_yn ? <Badge>공지</Badge> : "-"}</td>
              <td className="px-4 py-3 tabular-nums">{post.view_count}</td>
              <td className="px-4 py-3 tabular-nums">{post.comment_count}</td>
              <td className="px-4 py-3 text-muted-foreground">{formatDate(post.created_at)}</td>
              <td className="px-4 py-3">
                <Badge>{post.del_yn ? "삭제됨" : "게시중"}</Badge>
              </td>
              <td className="px-4 py-3">
                <Button
                  aria-label="게시글 상세"
                  variant="ghost"
                  size="icon"
                  onClick={() => onDetail(post.id)}
                >
                  <Eye />
                </Button>
                {post.del_yn ? (
                  <Button
                    aria-label="게시글 복구"
                    variant="ghost"
                    size="icon"
                    disabled={isPending}
                    onClick={() => onRestore(post)}
                  >
                    <RotateCcw />
                  </Button>
                ) : (
                  <Button
                    aria-label="게시글 삭제"
                    variant="ghost"
                    size="icon"
                    disabled={isPending}
                    onClick={() => onDelete(post)}
                  >
                    <Trash2 />
                  </Button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
