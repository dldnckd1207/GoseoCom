import { useState } from "react";

import { RefreshCcw, RotateCcw } from "lucide-react";

import { BASE_URL } from "~/shared/api/client";
import { Button } from "~/shared/ui/button";

import type { AdminTranslationDetail } from "~/entities/translation/types";

interface TranslationDetailDialogProps {
  translation: AdminTranslationDetail | undefined;
  open: boolean;
  isLoading: boolean;
  isError: boolean;
  isPending: boolean;
  onRetryLoad: () => void;
  onClose: () => void;
  onRetryTranslation: (translation: AdminTranslationDetail) => void;
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
  NO_TEXT: "텍스트 없음",
};

const triggerLabels: Record<string, string> = {
  TRANSLATOR: "번역",
  AUTO_REPLY: "자동답변",
};

function getStatusLabel(value: string | null) {
  if (!value) return "-";
  return statusLabels[value] ?? value;
}

function getTriggerLabel(value: string) {
  return triggerLabels[value] ?? value;
}

function formatDateTime(value: string | null) {
  if (!value) return "-";
  return new Intl.DateTimeFormat("ko-KR", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function formatDuration(value: number | null) {
  if (value === null) return "-";
  if (value < 1000) return `${value}ms`;
  return `${(value / 1000).toFixed(1)}초`;
}

function resolveFileUrl(path: string | null) {
  if (!path) return null;
  if (path.startsWith("http://") || path.startsWith("https://")) return path;
  return `${BASE_URL}${path}`;
}

function ReadOnlyField({ label, value }: { label: string; value: string }) {
  return (
    <label className="space-y-1 text-sm font-medium">
      <span>{label}</span>
      <input
        value={value}
        readOnly
        className="h-10 w-full rounded-md border border-border bg-muted px-3 text-sm text-muted-foreground outline-none"
      />
    </label>
  );
}

function OwnerField({ name, isSelf }: { name: string; isSelf: boolean }) {
  return (
    <div className="space-y-1 text-sm font-medium">
      <span>소유자</span>
      <div className="flex h-10 w-full items-center rounded-md border border-border bg-muted px-3 text-sm text-muted-foreground">
        <span>{name || "-"}</span>
        {isSelf ? (
          <span className="ml-2 rounded-full border border-border px-2 py-0.5 text-xs">본인</span>
        ) : null}
      </div>
    </div>
  );
}

function TextBlock({ label, value }: { label: string; value: string | null }) {
  return (
    <div className="space-y-2">
      <h4 className="text-sm font-medium">{label}</h4>
      <pre className="max-h-72 overflow-auto whitespace-pre-wrap break-words rounded-md border border-border bg-card p-3 font-sans text-sm text-muted-foreground">
        {value?.trim() ? value : "-"}
      </pre>
    </div>
  );
}

function PreviewDialog({
  translation,
  sourceFileUrl,
  onClose,
}: {
  translation: AdminTranslationDetail;
  sourceFileUrl: string | null;
  onClose: () => void;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 px-4">
      <div className="max-h-[92vh] w-full max-w-6xl overflow-y-auto rounded-md border border-border bg-card p-6">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h3 className="text-lg font-medium">번역 결과보기</h3>
            <p className="mt-1 text-sm text-muted-foreground">{translation.title}</p>
          </div>
          <Button type="button" variant="ghost" onClick={onClose}>
            닫기
          </Button>
        </div>

        {sourceFileUrl ? (
          <section className="mt-6 rounded-md border border-border bg-secondary p-4">
            <h4 className="text-sm font-medium">원본 이미지</h4>
            <div className="mt-3 overflow-hidden rounded-md border border-border bg-card">
              <img
                src={sourceFileUrl}
                alt={`${translation.title} 원본 이미지`}
                className="max-h-[420px] w-full object-contain"
              />
            </div>
          </section>
        ) : null}

        <section className="mt-4 space-y-4">
          {translation.pages.map((page) => (
            <details
              key={page.page_no}
              className="rounded-md border border-border bg-secondary p-4"
              open={translation.pages.length === 1}
            >
              <summary className="cursor-pointer text-sm font-medium">
                {page.page_no}페이지
              </summary>
              <div className="mt-4 grid gap-4 lg:grid-cols-3">
                <TextBlock label="OCR 원문" value={page.ocr_text} />
                <TextBlock label="직역" value={page.literal_text} />
                <TextBlock label="의역" value={page.interpretive_text} />
              </div>
            </details>
          ))}
        </section>

        <div className="mt-6 flex justify-end border-t border-border pt-4">
          <Button type="button" onClick={onClose}>
            확인
          </Button>
        </div>
      </div>
    </div>
  );
}

export function TranslationDetailDialog({
  translation,
  open,
  isLoading,
  isError,
  isPending,
  onRetryLoad,
  onClose,
  onRetryTranslation,
}: TranslationDetailDialogProps) {
  const [previewOpen, setPreviewOpen] = useState(false);

  if (!open) return null;
  const sourceFileUrl = resolveFileUrl(translation?.source_file_url ?? null);

  function handleClose() {
    setPreviewOpen(false);
    onClose();
  }

  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/70 px-4">
      <div className="max-h-[90vh] w-full max-w-5xl overflow-y-auto rounded-md border border-border bg-card p-6">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 className="text-lg font-medium">번역 이력 상세</h2>
            <p className="mt-1 text-sm text-muted-foreground">
              페이지별 처리 상태와 최근 파이프라인 실행 이력을 확인합니다.
            </p>
          </div>
          <Button type="button" variant="ghost" onClick={handleClose}>
            닫기
          </Button>
        </div>

        {isError ? (
          <div className="mt-6 flex items-center justify-between rounded-md border border-border bg-muted p-5">
            <p className="text-sm text-muted-foreground">
              번역 이력 상세를 불러오지 못했습니다.
            </p>
            <Button type="button" variant="outline" onClick={onRetryLoad}>
              <RefreshCcw />
              다시 시도
            </Button>
          </div>
        ) : isLoading || !translation ? (
          <div className="mt-6 rounded-md border border-border bg-muted p-8 text-sm text-muted-foreground">
            번역 이력 상세를 불러오는 중입니다.
          </div>
        ) : (
          <>
            <div className="mt-6 grid gap-4 md:grid-cols-3">
              <ReadOnlyField label="제목" value={translation.title} />
              <OwnerField name={translation.owner_name} isSelf={translation.owner_is_self} />
              <ReadOnlyField label="상태" value={getStatusLabel(translation.status)} />
              <ReadOnlyField label="원본 유형" value={translation.source_type} />
              <ReadOnlyField label="페이지 수" value={String(translation.total_pages)} />
              <ReadOnlyField label="Book 유형" value={translation.book_type} />
              <ReadOnlyField label="생성일" value={formatDateTime(translation.created_at)} />
              <ReadOnlyField label="수정일" value={formatDateTime(translation.updated_at)} />
              <ReadOnlyField
                label="재시도"
                value={translation.can_retry ? "가능" : (translation.retry_disabled_reason ?? "불가")}
              />
            </div>

            <section className="mt-6 rounded-md border border-border bg-secondary p-4">
              <h3 className="text-sm font-medium">페이지별 상태</h3>
              <div className="mt-3 overflow-x-auto">
                <table className="w-full min-w-[760px] text-left text-sm">
                  <thead className="border-b border-border text-xs text-muted-foreground">
                    <tr>
                      <th className="px-3 py-2 font-medium">페이지</th>
                      <th className="px-3 py-2 font-medium">상태</th>
                      <th className="px-3 py-2 font-medium">OCR</th>
                      <th className="px-3 py-2 font-medium">직역</th>
                      <th className="px-3 py-2 font-medium">의역</th>
                      <th className="px-3 py-2 font-medium">OCR 엔진</th>
                      <th className="px-3 py-2 font-medium">번역 엔진</th>
                    </tr>
                  </thead>
                  <tbody>
                    {translation.pages.map((page) => (
                      <tr key={page.page_no} className="border-b border-border last:border-b-0">
                        <td className="px-3 py-2 tabular-nums">{page.page_no}</td>
                        <td className="px-3 py-2">{getStatusLabel(page.status)}</td>
                        <td className="px-3 py-2">{page.has_ocr_text ? "있음" : "-"}</td>
                        <td className="px-3 py-2">{page.has_literal_text ? "있음" : "-"}</td>
                        <td className="px-3 py-2">
                          {page.has_interpretive_text ? "있음" : "-"}
                        </td>
                        <td className="px-3 py-2 text-muted-foreground">
                          {page.ocr_engine ?? "-"}
                        </td>
                        <td className="px-3 py-2 text-muted-foreground">
                          {page.translator_engine ?? "-"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>

            <section className="mt-4 rounded-md border border-border bg-secondary p-4">
              <h3 className="text-sm font-medium">최근 실행 이력</h3>
              <div className="mt-3 space-y-3">
                {translation.pipeline_runs.length === 0 ? (
                  <p className="text-sm text-muted-foreground">실행 이력이 없습니다.</p>
                ) : (
                  translation.pipeline_runs.map((run) => (
                    <div key={run.id} className="rounded-md border border-border bg-card p-3">
                      <div className="grid gap-3 text-sm md:grid-cols-5">
                        <span>{getTriggerLabel(run.trigger_type)}</span>
                        <span>{getStatusLabel(run.status)}</span>
                        <span className="text-muted-foreground">
                          {formatDateTime(run.started_at)}
                        </span>
                        <span className="text-muted-foreground">
                          {formatDateTime(run.completed_at)}
                        </span>
                        <span className="text-muted-foreground">
                          {formatDuration(run.duration_ms)}
                        </span>
                      </div>
                      {run.error_msg ? (
                        <p className="mt-2 text-sm text-destructive">{run.error_msg}</p>
                      ) : null}
                    </div>
                  ))
                )}
              </div>
            </section>

            <div className="mt-6 flex justify-end gap-2 border-t border-border pt-4">
              <Button type="button" variant="outline" onClick={handleClose}>
                닫기
              </Button>
              <Button type="button" variant="outline" onClick={() => setPreviewOpen(true)}>
                결과보기
              </Button>
              <Button
                type="button"
                disabled={isPending || !translation.can_retry}
                onClick={() => onRetryTranslation(translation)}
              >
                <RotateCcw />
                재시도
              </Button>
            </div>
            {previewOpen ? (
              <PreviewDialog
                translation={translation}
                sourceFileUrl={sourceFileUrl}
                onClose={() => setPreviewOpen(false)}
              />
            ) : null}
          </>
        )}
      </div>
    </div>
  );
}
