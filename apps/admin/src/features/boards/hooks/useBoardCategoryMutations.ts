import { useMutation, useQueryClient } from "@tanstack/react-query";

import { boardApi } from "~/features/boards/api/boardApi";

import type { AdminBoardCategorySaveRequest } from "~/entities/board/types";

function useInvalidateBoardCategories(boardId: string) {
  const queryClient = useQueryClient();

  return () => {
    void queryClient.invalidateQueries({ queryKey: ["admin", "boards", boardId, "categories"] });
  };
}

export function useCreateBoardCategory(boardId: string) {
  const invalidate = useInvalidateBoardCategories(boardId);

  return useMutation({
    mutationFn: (request: AdminBoardCategorySaveRequest) =>
      boardApi.createCategory(boardId, request),
    onSuccess: invalidate,
  });
}

export function useUpdateBoardCategory(boardId: string) {
  const invalidate = useInvalidateBoardCategories(boardId);

  return useMutation({
    mutationFn: ({
      categoryId,
      request,
    }: {
      categoryId: string;
      request: AdminBoardCategorySaveRequest;
    }) => boardApi.updateCategory(boardId, categoryId, request),
    onSuccess: invalidate,
  });
}

export function useDeleteBoardCategory(boardId: string) {
  const invalidate = useInvalidateBoardCategories(boardId);

  return useMutation({
    mutationFn: (categoryId: string) => boardApi.removeCategory(boardId, categoryId),
    onSuccess: invalidate,
  });
}
