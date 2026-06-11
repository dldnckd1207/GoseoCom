import { useQuery } from "@tanstack/react-query";

import { boardApi } from "~/features/boards/api/boardApi";

interface UseAdminBoardsParams {
  keyword: string;
  useYn: "all" | "active" | "inactive";
  page: number;
  size?: number;
}

export function useAdminBoards({ keyword, useYn, page, size = 10 }: UseAdminBoardsParams) {
  return useQuery({
    queryKey: ["admin", "boards", { keyword, useYn, page, size }],
    queryFn: () =>
      boardApi.list({
        keyword: keyword.trim() || null,
        use_yn: useYn === "all" ? null : useYn === "active",
        page,
        size,
      }),
  });
}
