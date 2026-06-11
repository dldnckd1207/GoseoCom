import { RefreshCcw } from "lucide-react";

import { Button } from "~/shared/ui/button";

import type { AdminPostDetail } from "~/entities/post/types";

interface PostDetailDialogProps {
  post: AdminPostDetail | undefined;
  open: boolean;
  isLoading: boolean;
  isError: boolean;
  isPending: boolean;
  onRetry: () => void;
  onClose: () => void;
  onDelete: (post: AdminPostDetail) => void;
  onRestore: (post: AdminPostDetail) => void;
}

function formatDateTime(value: string | null) {
  if (!value) return "-";
  return new Intl.DateTimeFormat("ko-KR", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function ReadOnlyField({ label, value }: { label: string; value: string }) {
  return (
    <label className="space-y-1 text-sm font-medium">
      <span>{label}</span>
      <input
        value={value}
        readOnly
        className="h-10 w-full rounded-md border border-border bg-muted px-3 text-sm text-muted-foreground outline-none"
      />
    </label>
  );
}

export function PostDetailDialog({
  post,
  open,
  isLoading,
  isError,
  isPending,
  onRetry,
  onClose,
  onDelete,
  onRestore,
}: PostDetailDialogProps) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/70 px-4">
      <div className="max-h-[90vh] w-full max-w-4xl overflow-y-auto rounded-md border border-border bg-card p-6">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 className="text-lg font-medium">게시글 상세</h2>
            <p className="mt-1 text-sm text-muted-foreground">
              관리자 조회는 게시글 조회 수에 반영되지 않습니다.
            </p>
          </div>
          <Button type="button" variant="ghost" onClick={onClose}>
            닫기
          </Button>
        </div>

        {isError ? (
          <div className="mt-6 flex items-center justify-between rounded-md border border-border bg-muted p-5">
            <p className="text-sm text-muted-foreground">
              게시글 상세를 불러오지 못했습니다.
            </p>
            <Button type="button" variant="outline" onClick={onRetry}>
              <RefreshCcw />
              다시 시도
            </Button>
          </div>
        ) : isLoading || !post ? (
          <div className="mt-6 rounded-md border border-border bg-muted p-8 text-sm text-muted-foreground">
            게시글 상세를 불러오는 중입니다.
          </div>
        ) : (
          <>
            <div className="mt-6 grid gap-4 md:grid-cols-3">
              <ReadOnlyField label="게시판" value={post.board_name} />
              <ReadOnlyField label="카테고리" value={post.category_name ?? "-"} />
              <ReadOnlyField label="상태" value={post.del_yn ? "삭제됨" : "게시중"} />
              <ReadOnlyField label="작성자" value={`${post.author_name} (${post.user_id})`} />
              <ReadOnlyField label="작성일" value={formatDateTime(post.created_at)} />
              <ReadOnlyField label="수정일" value={formatDateTime(post.updated_at)} />
              <ReadOnlyField label="조회 수" value={String(post.view_count)} />
              <ReadOnlyField label="댓글 수" value={String(post.comment_count)} />
              <ReadOnlyField label="공지 여부" value={post.notice_yn ? "공지" : "일반"} />
            </div>

            <div className="mt-6 space-y-1 text-sm font-medium">
              <span>제목</span>
              <input
                value={post.title}
                readOnly
                className="h-10 w-full rounded-md border border-border bg-muted px-3 text-sm text-muted-foreground outline-none"
              />
            </div>

            <div className="mt-4 space-y-1 text-sm font-medium">
              <span>본문</span>
              <div className="min-h-40 whitespace-pre-wrap rounded-md border border-border bg-muted px-3 py-2 text-sm text-muted-foreground">
                {post.content}
              </div>
            </div>

            <div className="mt-4 grid gap-4 md:grid-cols-2">
              <div className="rounded-md border border-border bg-secondary p-4">
                <h3 className="text-sm font-medium">첨부파일</h3>
                <div className="mt-3 space-y-2 text-sm text-muted-foreground">
                  {post.files.length === 0 ? (
                    <p>첨부파일이 없습니다.</p>
                  ) : (
                    post.files.map((file) => <p key={file.file_id}>{file.original_name}</p>)
                  )}
                </div>
              </div>
              <div className="rounded-md border border-border bg-secondary p-4">
                <h3 className="text-sm font-medium">연결 번역 이력</h3>
                <div className="mt-3 space-y-1 text-sm text-muted-foreground">
                  {post.book ? (
                    <>
                      <p>{post.book.title}</p>
                      <p className="font-mono text-xs">{post.book.book_id}</p>
                      <p>{post.book.summary_text ?? "요약 없음"}</p>
                    </>
                  ) : (
                    <p>연결된 번역 이력이 없습니다.</p>
                  )}
                </div>
              </div>
            </div>

            {post.del_yn ? (
              <div className="mt-4 rounded-md border border-destructive/40 bg-destructive/10 p-4 text-sm">
                <p className="font-medium">삭제 정보</p>
                <p className="mt-1 text-muted-foreground">
                  {formatDateTime(post.deleted_at)} · {post.deleted_by_name ?? post.deleted_by ?? "-"}
                </p>
              </div>
            ) : null}

            <div className="mt-6 flex justify-end gap-2 border-t border-border pt-4">
              <Button type="button" variant="outline" onClick={onClose}>
                닫기
              </Button>
              {post.del_yn ? (
                <Button type="button" disabled={isPending} onClick={() => onRestore(post)}>
                  복구
                </Button>
              ) : (
                <Button
                  type="button"
                  variant="destructive"
                  disabled={isPending}
                  onClick={() => onDelete(post)}
                >
                  삭제
                </Button>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
