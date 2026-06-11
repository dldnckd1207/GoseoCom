import { useQuery } from "@tanstack/react-query";

import { commentApi } from "~/features/comments/api";

interface Params {
  keyword: string;
  page: number;
}

export function useFilteredComments({ keyword, page }: Params) {
  return useQuery({
    queryKey: ["admin", "comments", "filtered", { keyword, page }],
    queryFn: () =>
      commentApi.list({
        keyword: keyword.trim() || null,
        page,
        size: 20,
      }),
  });
}
