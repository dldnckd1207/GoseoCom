import { Eye, RefreshCcw, RotateCcw } from "lucide-react";

import { Button } from "~/shared/ui/button";

import type { AdminTranslationListItem } from "~/entities/translation/types";

interface TranslationTableProps {
  translations: AdminTranslationListItem[];
  isLoading: boolean;
  isError: boolean;
  isPending: boolean;
  rowNumberStart: number;
  onRetryList: () => void;
  onDetail: (bookId: string) => void;
  onRetryTranslation: (translation: AdminTranslationListItem) => void;
}

const statusLabels: Record<string, string> = {
  PENDING: "대기",
  OCR_PROCESSING: "OCR 처리중",
  OCR_COMPLETED: "OCR 완료",
  TRANSLATING: "번역중",
  COMPLETED: "완료",
  FAILED: "실패",
  RUNNING: "실행중",
  TIMEOUT: "시간초과",
};

function formatDate(value: string | null) {
  if (!value) return "-";
  return new Intl.DateTimeFormat("ko-KR", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(new Date(value));
}

function Badge({ children }: { children: string }) {
  return <span className="rounded-full border border-border px-2 py-1 text-xs">{children}</span>;
}

function getStatusLabel(value: string | null) {
  if (!value) return "-";
  return statusLabels[value] ?? value;
}

export function TranslationTable({
  translations,
  isLoading,
  isError,
  isPending,
  rowNumberStart,
  onRetryList,
  onDetail,
  onRetryTranslation,
}: TranslationTableProps) {
  if (isLoading) {
    return (
      <div className="rounded-md border border-border bg-card p-8 text-sm text-muted-foreground">
        번역 이력을 불러오는 중입니다.
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex items-center justify-between rounded-md border border-border bg-card p-5">
        <p className="text-sm text-muted-foreground">번역 이력을 불러오지 못했습니다.</p>
        <Button variant="outline" onClick={onRetryList}>
          <RefreshCcw />
          다시 시도
        </Button>
      </div>
    );
  }

  if (translations.length === 0) {
    return (
      <div className="rounded-md border border-border bg-card p-8 text-sm text-muted-foreground">
        조건에 맞는 번역 이력이 없습니다.
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-md border border-border bg-card">
      <table className="w-full min-w-[980px] text-left text-sm">
        <thead className="border-b border-border bg-muted/60 text-xs uppercase tracking-[0.08em] text-muted-foreground">
          <tr>
            <th className="w-16 px-4 py-3 font-medium">순번</th>
            <th className="px-4 py-3 font-medium">제목</th>
            <th className="px-4 py-3 font-medium">소유자</th>
            <th className="px-4 py-3 font-medium">상태</th>
            <th className="px-4 py-3 font-medium">페이지</th>
            <th className="px-4 py-3 font-medium">생성일</th>
            <th className="px-4 py-3 font-medium">최근 실행</th>
            <th className="w-28 px-4 py-3 font-medium">관리</th>
          </tr>
        </thead>
        <tbody>
          {translations.map((translation, index) => (
            <tr key={translation.book_id} className="border-b border-border last:border-b-0">
              <td className="px-4 py-3 text-muted-foreground tabular-nums">
                {rowNumberStart - index}
              </td>
              <td className="px-4 py-3">
                <div className="max-w-[340px] truncate font-medium" title={translation.title}>
                  {translation.title}
                </div>
              </td>
              <td className="px-4 py-3">
                <span>{translation.owner_name || "-"}</span>
                {translation.owner_is_self ? (
                  <span className="ml-2 rounded-full border border-border px-2 py-0.5 text-xs text-muted-foreground">
                    본인
                  </span>
                ) : null}
              </td>
              <td className="px-4 py-3">
                <Badge>{getStatusLabel(translation.status)}</Badge>
              </td>
              <td className="px-4 py-3 tabular-nums">{translation.total_pages}</td>
              <td className="px-4 py-3 text-muted-foreground">
                {formatDate(translation.created_at)}
              </td>
              <td className="px-4 py-3 text-muted-foreground">
                <div className="max-w-[220px] truncate">
                  {getStatusLabel(translation.latest_run_status)}
                  {translation.latest_run_error_msg
                    ? ` · ${translation.latest_run_error_msg}`
                    : ""}
                </div>
              </td>
              <td className="px-4 py-3">
                <Button
                  aria-label="번역 상세"
                  variant="ghost"
                  size="icon"
                  onClick={() => onDetail(translation.book_id)}
                >
                  <Eye />
                </Button>
                <Button
                  aria-label="번역 재시도"
                  variant="ghost"
                  size="icon"
                  disabled={isPending || !translation.can_retry}
                  onClick={() => onRetryTranslation(translation)}
                >
                  <RotateCcw />
                </Button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
