import { useState } from "react";

import { emptyBoardForm } from "~/features/boards/lib/boardForm";

import { Button } from "~/shared/ui/button";
import { Switch } from "~/shared/ui/switch";

import type { FormEvent } from "react";
import type { AdminBoard } from "~/entities/board/types";
import type { BoardFormState } from "~/features/boards/lib/boardForm";

interface BoardFormDialogProps {
  mode: "create" | "edit";
  board: AdminBoard | null;
  open: boolean;
  isSaving: boolean;
  onClose: () => void;
  onSubmit: (form: BoardFormState) => void;
}

export function BoardFormDialog({
  mode,
  board,
  open,
  isSaving,
  onClose,
  onSubmit,
}: BoardFormDialogProps) {
  const [form, setForm] = useState<BoardFormState>(
    board ? { ...emptyBoardForm, ...formToState(board) } : emptyBoardForm,
  );

  if (!open) return null;

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    onSubmit(form);
  }

  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/70 px-4">
      <form
        className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-md border border-border bg-card p-6"
        onSubmit={handleSubmit}
      >
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 className="text-lg font-medium">{mode === "create" ? "게시판 등록" : "게시판 수정"}</h2>
            <p className="mt-1 text-sm text-muted-foreground">운영에 필요한 핵심 설정만 관리합니다.</p>
          </div>
          <Button type="button" variant="ghost" onClick={onClose}>
            닫기
          </Button>
        </div>

        <div className="mt-6 grid gap-4 md:grid-cols-2">
          <TextField
            label="게시판 코드"
            value={form.board_code}
            disabled={mode === "edit"}
            required
            onChange={(value) => setForm((current) => ({ ...current, board_code: value }))}
          />
          <TextField
            label="게시판 이름"
            value={form.board_name}
            required
            onChange={(value) => setForm((current) => ({ ...current, board_name: value }))}
          />
          <TextField
            label="게시판 그룹"
            value={form.board_group}
            onChange={(value) => setForm((current) => ({ ...current, board_group: value }))}
          />
          <label className="space-y-1 text-sm font-medium">
            <span>게시판 타입</span>
            <select
              value={form.board_type}
              className="h-10 w-full rounded-md border border-border bg-secondary px-3 text-sm outline-none focus:ring-3 focus:ring-ring/30"
              onChange={(event) =>
                setForm((current) => ({
                  ...current,
                  board_type: event.target.value as BoardFormState["board_type"],
                }))
              }
            >
              <option value="LIST">LIST</option>
            </select>
          </label>
          <label className="space-y-1 text-sm font-medium md:col-span-2">
            <span>게시판 설명</span>
            <textarea
              value={form.board_desc}
              className="min-h-24 w-full rounded-md border border-border bg-secondary px-3 py-2 text-sm outline-none focus:ring-3 focus:ring-ring/30"
              onChange={(event) =>
                setForm((current) => ({ ...current, board_desc: event.target.value }))
              }
            />
          </label>
        </div>

        <div className="mt-6 grid gap-4 md:grid-cols-3">
          <SwitchField
            label="사용 여부"
            checked={form.use_yn}
            activeLabel="사용"
            inactiveLabel="미사용"
            onChange={(checked) => setForm((current) => ({ ...current, use_yn: checked }))}
          />
          <SwitchField
            label="비회원 읽기"
            checked={form.guest_read_yn}
            activeLabel="허용"
            inactiveLabel="차단"
            onChange={(checked) =>
              setForm((current) => ({ ...current, guest_read_yn: checked }))
            }
          />
          <SwitchField
            label="회원 쓰기"
            checked={form.write_yn}
            activeLabel="허용"
            inactiveLabel="차단"
            onChange={(checked) => setForm((current) => ({ ...current, write_yn: checked }))}
          />
          <SwitchField
            label="댓글 사용"
            checked={form.comment_yn}
            activeLabel="사용"
            inactiveLabel="미사용"
            onChange={(checked) => setForm((current) => ({ ...current, comment_yn: checked }))}
          />
          <SwitchField
            label="카테고리 사용"
            checked={form.category_yn}
            activeLabel="사용"
            inactiveLabel="미사용"
            onChange={(checked) => setForm((current) => ({ ...current, category_yn: checked }))}
          />
          <SwitchField
            label="첨부 사용"
            checked={form.attach_yn}
            activeLabel="사용"
            inactiveLabel="미사용"
            onChange={(checked) =>
              setForm((current) => ({
                ...current,
                attach_yn: checked,
                attach_ext: checked ? current.attach_ext : "",
              }))
            }
          />
          <SwitchField
            label="AI 자동답변"
            checked={form.auto_reply_enabled}
            activeLabel="사용"
            inactiveLabel="미사용"
            onChange={(checked) =>
              setForm((current) => ({ ...current, auto_reply_enabled: checked }))
            }
          />
        </div>

        <div className="mt-4 grid gap-4 md:grid-cols-2">
          <TextField
            label="허용 확장자"
            value={form.attach_ext}
            required={form.attach_yn}
            disabled={!form.attach_yn}
            onChange={(value) => setForm((current) => ({ ...current, attach_ext: value }))}
          />
        </div>

        <div className="mt-6 flex justify-end gap-2 border-t border-border pt-4">
          <Button type="button" variant="outline" onClick={onClose}>
            취소
          </Button>
          <Button type="submit" disabled={isSaving}>
            저장
          </Button>
        </div>
      </form>
    </div>
  );
}

function formToState(board: AdminBoard): BoardFormState {
  return {
    board_code: board.board_code,
    board_name: board.board_name,
    board_desc: board.board_desc ?? "",
    board_group: board.board_group ?? "",
    board_type: board.board_type,
    guest_read_yn: board.guest_read_yn,
    write_yn: board.write_yn,
    comment_yn: board.comment_yn,
    category_yn: board.category_yn,
    attach_yn: board.attach_yn,
    attach_ext: board.attach_ext ?? "",
    auto_reply_enabled: board.auto_reply_enabled,
    use_yn: board.use_yn,
    sort_order: board.sort_order,
  };
}

interface TextFieldProps {
  label: string;
  value: string;
  type?: "text" | "number";
  required?: boolean;
  disabled?: boolean;
  onChange: (value: string) => void;
}

function TextField({ label, value, type = "text", required, disabled, onChange }: TextFieldProps) {
  return (
    <label className="space-y-1 text-sm font-medium">
      <span>{label}</span>
      <input
        value={value}
        type={type}
        required={required}
        disabled={disabled}
        className="h-10 w-full rounded-md border border-border bg-secondary px-3 text-sm outline-none focus:ring-3 focus:ring-ring/30 disabled:bg-muted"
        onChange={(event) => onChange(event.target.value)}
      />
    </label>
  );
}

interface SwitchFieldProps {
  label: string;
  checked: boolean;
  activeLabel: string;
  inactiveLabel: string;
  onChange: (checked: boolean) => void;
}

function SwitchField({ label, checked, activeLabel, inactiveLabel, onChange }: SwitchFieldProps) {
  const currentLabel = checked ? activeLabel : inactiveLabel;

  return (
    <div className="space-y-1 text-sm font-medium">
      <div className="flex items-center justify-between gap-2">
        <span>{label}</span>
        <span className="rounded-full border border-border px-2 py-0.5 text-xs text-muted-foreground">
          {currentLabel}
        </span>
      </div>
      <div className="flex h-10 w-full items-center justify-between rounded-md border border-border bg-secondary px-3 text-sm">
        <span className="text-muted-foreground">{currentLabel}</span>
        <Switch checked={checked} onCheckedChange={onChange} />
      </div>
    </div>
  );
}
