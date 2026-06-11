import { useQuery } from "@tanstack/react-query";

import { boardApi } from "~/features/boards/api/boardApi";

export function useBoardCategories(boardId: string | null, enabled: boolean) {
  return useQuery({
    queryKey: ["admin", "boards", boardId, "categories"],
    queryFn: () => boardApi.listCategories(boardId ?? ""),
    enabled: enabled && Boolean(boardId),
  });
}
