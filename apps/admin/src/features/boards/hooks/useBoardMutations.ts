import { useMutation, useQueryClient } from "@tanstack/react-query";

import { boardApi } from "~/features/boards/api/boardApi";

import type { AdminBoardSaveRequest } from "~/entities/board/types";

export function useCreateBoard() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: AdminBoardSaveRequest) => boardApi.create(request),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["admin", "boards"] });
    },
  });
}

export function useUpdateBoard() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ boardId, request }: { boardId: string; request: AdminBoardSaveRequest }) =>
      boardApi.update(boardId, request),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["admin", "boards"] });
    },
  });
}
