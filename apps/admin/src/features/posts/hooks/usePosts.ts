import { useQuery } from "@tanstack/react-query";

import { postApi } from "~/features/posts/api/postApi";

import type { AdminPostDeletedStatus } from "~/entities/post/types";

interface UsePostsParams {
  keyword: string;
  boardId: string;
  authorKeyword: string;
  noticeYn: "all" | "notice" | "normal";
  deletedStatus: AdminPostDeletedStatus;
  page: number;
}

export function usePosts({
  keyword,
  boardId,
  authorKeyword,
  noticeYn,
  deletedStatus,
  page,
}: UsePostsParams) {
  return useQuery({
    queryKey: [
      "admin",
      "posts",
      { keyword, boardId, authorKeyword, noticeYn, deletedStatus, page },
    ],
    queryFn: () =>
      postApi.list({
        keyword: keyword.trim() || null,
        board_id: boardId || null,
        author_keyword: authorKeyword.trim() || null,
        notice_yn: noticeYn === "all" ? null : noticeYn === "notice",
        deleted_status: deletedStatus,
        page,
        size: 10,
      }),
  });
}
