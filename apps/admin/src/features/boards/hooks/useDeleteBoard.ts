import { useMutation, useQueryClient } from "@tanstack/react-query";

import { boardApi } from "~/features/boards/api/boardApi";

export function useDeleteBoard() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: boardApi.remove,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["admin", "boards"] });
    },
  });
}
