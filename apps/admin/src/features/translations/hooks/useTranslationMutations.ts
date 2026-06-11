import { useMutation, useQueryClient } from "@tanstack/react-query";

import { translationApi } from "~/features/translations/api/translationApi";

export function useRetryTranslation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (bookId: string) => translationApi.retry(bookId),
    onSuccess: (_data, bookId) => {
      void queryClient.invalidateQueries({ queryKey: ["admin", "translations"] });
      void queryClient.invalidateQueries({
        queryKey: ["admin", "translations", "detail", bookId],
      });
    },
  });
}
