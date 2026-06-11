import { useQuery } from "@tanstack/react-query";

import { postApi } from "~/features/posts/api/postApi";

export function usePostDetail(postId: string | null) {
  return useQuery({
    queryKey: ["admin", "posts", "detail", postId],
    queryFn: () => postApi.get(postId ?? ""),
    enabled: Boolean(postId),
  });
}
