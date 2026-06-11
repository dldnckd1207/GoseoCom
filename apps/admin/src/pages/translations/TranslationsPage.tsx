import { useState } from "react";

import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight } from "lucide-react";

import { useTranslationDetail } from "~/features/translations/hooks/useTranslationDetail";
import { useRetryTranslation } from "~/features/translations/hooks/useTranslationMutations";
import { useTranslations } from "~/features/translations/hooks/useTranslations";
import { TranslationDetailDialog } from "~/features/translations/ui/TranslationDetailDialog";
import { TranslationFilterBar } from "~/features/translations/ui/TranslationFilterBar";
import { TranslationTable } from "~/features/translations/ui/TranslationTable";

import { ApiError } from "~/shared/api/client";
import { openModal } from "~/shared/stores/modalStore";
import { Button } from "~/shared/ui/button";

import type {
  AdminTranslationDetail,
  AdminTranslationListItem,
  AdminTranslationStatus,
} from "~/entities/translation/types";

function getPageNumbers(currentPage: number, totalPages: number) {
  const groupStart = Math.floor((currentPage - 1) / 10) * 10 + 1;
  const groupEnd = Math.min(totalPages, groupStart + 9);

  return Array.from({ length: groupEnd - groupStart + 1 }, (_, index) => groupStart + index);
}

export function TranslationsPage() {
  const [keyword, setKeyword] = useState("");
  const [status, setStatus] = useState<AdminTranslationStatus>("all");
  const [page, setPage] = useState(1);
  const [detailBookId, setDetailBookId] = useState<string | null>(null);

  const translationsQuery = useTranslations({ keyword, status, page });
  const detailQuery = useTranslationDetail(detailBookId);
  const retryTranslation = useRetryTranslation();

  const data = translationsQuery.data;
  const totalPages = data ? Math.max(1, Math.ceil(data.total / data.size)) : 1;
  const pageNumbers = getPageNumbers(page, totalPages);

  function resetPage() {
    setPage(1);
  }

  function handleRetry(translation: AdminTranslationListItem | AdminTranslationDetail) {
    openModal({
      type: "confirm",
      title: "번역 재시도",
      message:
        "실패한 번역을 원본 파일로 다시 처리합니다.\n기존 페이지 결과는 초기화되고 새 실행 이력이 생성됩니다.",
      buttons: [
        { label: "취소", variant: "outline" },
        {
          label: "재시도",
              onClick: () => {
                retryTranslation.mutate(translation.book_id, {
                  onSuccess: () => {
                    if (detailBookId === translation.book_id) {
                      setDetailBookId(null);
                    }
                    openModal({ type: "alert", message: "번역 재시도를 시작했습니다." });
                  },
              onError: (error) => {
                openModal({
                  type: "error",
                  message:
                    error instanceof ApiError ? error.message : "번역을 재시도하지 못했습니다.",
                });
              },
            });
          },
        },
      ],
    });
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-medium tracking-normal">번역 이력</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          전체 OCR/번역 이력을 조회하고 실패한 번역을 재시도합니다.
        </p>
      </div>

      <TranslationFilterBar
        keyword={keyword}
        status={status}
        onKeywordChange={(value) => {
          setKeyword(value);
          resetPage();
        }}
        onStatusChange={(value) => {
          setStatus(value);
          resetPage();
        }}
      />

      <TranslationTable
        translations={data?.items ?? []}
        isLoading={translationsQuery.isLoading}
        isError={translationsQuery.isError}
        isPending={retryTranslation.isPending}
        rowNumberStart={(data?.total ?? 0) - (page - 1) * (data?.size ?? 10)}
        onRetryList={() => void translationsQuery.refetch()}
        onDetail={(bookId) => setDetailBookId(bookId)}
        onRetryTranslation={handleRetry}
      />

      <div className="flex flex-col gap-3 text-sm text-muted-foreground md:flex-row md:items-center md:justify-between">
        <span>총 {data?.total ?? 0}개</span>
        <div className="flex flex-wrap items-center gap-1">
          <Button
            variant="outline"
            size="icon"
            className="size-8"
            disabled={page <= 1}
            onClick={() => setPage(1)}
            aria-label="첫 페이지"
          >
            <ChevronsLeft />
          </Button>
          <Button
            variant="outline"
            size="icon"
            className="size-8"
            disabled={page <= 1}
            onClick={() => setPage((current) => Math.max(1, current - 1))}
            aria-label="이전 페이지"
          >
            <ChevronLeft />
          </Button>
          {pageNumbers.map((pageNumber) => (
            <Button
              key={pageNumber}
              variant={pageNumber === page ? "default" : "outline"}
              size="sm"
              className="size-8 px-0 tabular-nums"
              onClick={() => setPage(pageNumber)}
              aria-current={pageNumber === page ? "page" : undefined}
            >
              {pageNumber}
            </Button>
          ))}
          <Button
            variant="outline"
            size="icon"
            className="size-8"
            disabled={page >= totalPages}
            onClick={() => setPage((current) => Math.min(totalPages, current + 1))}
            aria-label="다음 페이지"
          >
            <ChevronRight />
          </Button>
          <Button
            variant="outline"
            size="icon"
            className="size-8"
            disabled={page >= totalPages}
            onClick={() => setPage(totalPages)}
            aria-label="마지막 페이지"
          >
            <ChevronsRight />
          </Button>
        </div>
      </div>

      <TranslationDetailDialog
        translation={detailQuery.data}
        open={detailBookId !== null}
        isLoading={detailQuery.isLoading}
        isError={detailQuery.isError}
        isPending={retryTranslation.isPending}
        onRetryLoad={() => void detailQuery.refetch()}
        onClose={() => setDetailBookId(null)}
        onRetryTranslation={handleRetry}
      />
    </div>
  );
}
