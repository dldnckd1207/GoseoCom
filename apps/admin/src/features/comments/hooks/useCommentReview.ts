import { useMutation, useQueryClient } from "@tanstack/react-query";

import { commentApi } from "~/features/comments/api";

export function useApproveComment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (commentId: string) => commentApi.approve(commentId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["admin", "comments", "filtered"] });
    },
  });
}

export function useRejectComment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (commentId: string) => commentApi.reject(commentId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["admin", "comments", "filtered"] });
    },
  });
}
