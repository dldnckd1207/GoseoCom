import { useMutation, useQueryClient } from "@tanstack/react-query";

import { postApi } from "~/features/posts/api/postApi";

export function useDeletePost() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (postId: string) => postApi.remove(postId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["admin", "posts"] });
    },
  });
}

export function useRestorePost() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (postId: string) => postApi.restore(postId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["admin", "posts"] });
    },
  });
}
