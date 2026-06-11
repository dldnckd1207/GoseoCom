import { useEffect } from "react";

import { useForm, useWatch } from "react-hook-form";

import { z } from "zod";

import {
  canChangeLevel,
  canChangeStatus,
  canForceWithdraw,
} from "~/features/users/lib/userRole";

import { Button } from "~/shared/ui/button";
import { Switch } from "~/shared/ui/switch";

import type { AdminUserDetail, AdminUserUpdateRequest } from "~/entities/user/types";

const updateSchema = z.object({
  user_level: z.union([z.literal(10), z.literal(70), z.literal(100)]),
  use_yn: z.boolean(),
  block_yn: z.boolean(),
});

const withdrawSchema = z.object({
  left_reason: z.string().trim().min(1, "강제 탈퇴 사유를 입력해주세요.").max(500),
});

type UserFormValues = z.infer<typeof updateSchema> & z.infer<typeof withdrawSchema>;

interface UserFormDialogProps {
  user: AdminUserDetail | null;
  sessionLevel: number | undefined;
  open: boolean;
  isSaving: boolean;
  isWithdrawing: boolean;
  onClose: () => void;
  onSubmit: (request: AdminUserUpdateRequest) => void;
  onForceWithdraw: (reason: string) => void;
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

export function UserFormDialog({
  user,
  sessionLevel,
  open,
  isSaving,
  isWithdrawing,
  onClose,
  onSubmit,
  onForceWithdraw,
}: UserFormDialogProps) {
  const form = useForm<UserFormValues>({
    defaultValues: {
      user_level: 10,
      use_yn: true,
      block_yn: false,
      left_reason: "",
    },
  });
  const useYn = useWatch({ control: form.control, name: "use_yn" });
  const blockYn = useWatch({ control: form.control, name: "block_yn" });

  useEffect(() => {
    if (!user) return;
    form.reset({
      user_level: user.user_level === 100 ? 100 : user.user_level === 70 ? 70 : 10,
      use_yn: user.use_yn,
      block_yn: user.block_yn,
      left_reason: "",
    });
  }, [form, user]);

  if (!open || !user) return null;

  const currentUser = user;
  const levelEditable = canChangeLevel(sessionLevel, currentUser.is_self, currentUser.del_yn);
  const statusEditable = canChangeStatus(
    sessionLevel,
    currentUser.user_level,
    currentUser.is_self,
    currentUser.del_yn,
  );
  const withdrawable = canForceWithdraw(sessionLevel, currentUser.is_self, currentUser.del_yn);
  const disabledReason = getDisabledReason(currentUser);
  function handleSubmit(values: UserFormValues) {
    const parsed = updateSchema.safeParse(values);
    if (!parsed.success) return;
    const request: AdminUserUpdateRequest = {};
    if (levelEditable && parsed.data.user_level !== currentUser.user_level) {
      request.user_level = parsed.data.user_level;
    }
    if (parsed.data.use_yn !== currentUser.use_yn) {
      request.use_yn = parsed.data.use_yn;
    }
    if (parsed.data.block_yn !== currentUser.block_yn) {
      request.block_yn = parsed.data.block_yn;
    }
    onSubmit(request);
  }

  function handleWithdraw() {
    const parsed = withdrawSchema.safeParse({ left_reason: form.getValues("left_reason") });
    if (!parsed.success) {
      form.setError("left_reason", { message: parsed.error.issues[0]?.message });
      return;
    }
    onForceWithdraw(parsed.data.left_reason);
  }

  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/70 px-4">
      <form
        className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-md border border-border bg-card p-6"
        onSubmit={form.handleSubmit(handleSubmit)}
      >
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 className="text-lg font-medium">사용자 상세</h2>
            <p className="mt-1 text-sm text-muted-foreground">
              계정 상태와 관리자 권한을 관리합니다.
            </p>
          </div>
          <Button type="button" variant="ghost" onClick={onClose}>
            닫기
          </Button>
        </div>

        <div className="mt-6 grid gap-4 md:grid-cols-2">
          <ReadOnlyField label="이름" value={user.name} />
          <ReadOnlyField label="이메일" value={user.email} />
          <ReadOnlyField label="가입일" value={formatDateTime(user.joined_at)} />
          <ReadOnlyField label="마지막 로그인" value={formatDateTime(user.last_login_at)} />
        </div>

        <div className="mt-6 grid gap-4 md:grid-cols-3">
          <ToggleField
            label="사용 여부"
            checked={useYn}
            activeLabel="사용"
            inactiveLabel="미사용"
            disabled={!statusEditable}
            onChange={(checked) => form.setValue("use_yn", checked, { shouldDirty: true })}
          />
          <ToggleField
            label="차단 여부"
            checked={blockYn}
            activeLabel="차단"
            inactiveLabel="정상"
            disabled={!statusEditable}
            onChange={(checked) => form.setValue("block_yn", checked, { shouldDirty: true })}
          />
          <label className="space-y-1 text-sm font-medium">
            <span>권한 레벨</span>
            <select
              disabled={!levelEditable}
              className="h-10 w-full rounded-md border border-border bg-secondary px-3 text-sm outline-none focus:ring-3 focus:ring-ring/30 disabled:bg-muted"
              {...form.register("user_level", { valueAsNumber: true })}
            >
              <option value={10}>사용자</option>
              <option value={70}>관리자</option>
              <option value={100}>슈퍼관리자</option>
            </select>
          </label>
        </div>

        <div className="mt-3 space-y-1 text-xs text-muted-foreground">
          {disabledReason ? <p>{disabledReason}</p> : null}
          {!levelEditable && !disabledReason ? (
            <p>권한 변경은 슈퍼관리자만 변경할 수 있습니다.</p>
          ) : null}
          {!withdrawable && !disabledReason ? (
            <p>강제 탈퇴는 슈퍼관리자만 수행할 수 있습니다.</p>
          ) : null}
        </div>

        <div className="mt-6 rounded-md border border-destructive/40 bg-destructive/10 p-4">
          <h3 className="text-sm font-medium">강제 탈퇴</h3>
          <p className="mt-1 text-sm text-muted-foreground">
            사용자는 로그인할 수 없게 되며 기본 목록에서 제외됩니다.
          </p>
          <textarea
            disabled={!withdrawable}
            className="mt-3 min-h-20 w-full rounded-md border border-border bg-secondary px-3 py-2 text-sm outline-none focus:ring-3 focus:ring-ring/30 disabled:bg-muted"
            placeholder="강제 탈퇴 사유"
            {...form.register("left_reason")}
          />
          {form.formState.errors.left_reason ? (
            <p className="mt-1 text-xs text-destructive">
              {form.formState.errors.left_reason.message}
            </p>
          ) : null}
          <Button
            type="button"
            variant="destructive"
            className="mt-3"
            disabled={!withdrawable || isWithdrawing}
            onClick={handleWithdraw}
          >
            강제 탈퇴
          </Button>
        </div>

        <div className="mt-6 flex justify-end gap-2 border-t border-border pt-4">
          <Button type="button" variant="outline" onClick={onClose}>
            취소
          </Button>
          <Button type="submit" disabled={isSaving || user.del_yn}>
            저장
          </Button>
        </div>
      </form>
    </div>
  );
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

interface ToggleFieldProps {
  label: string;
  checked: boolean;
  activeLabel: string;
  inactiveLabel: string;
  disabled: boolean;
  onChange: (checked: boolean) => void;
}

function ToggleField({
  label,
  checked,
  activeLabel,
  inactiveLabel,
  disabled,
  onChange,
}: ToggleFieldProps) {
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
        <span className="text-muted-foreground">{checked ? activeLabel : inactiveLabel}</span>
        <Switch checked={checked} disabled={disabled} onCheckedChange={onChange} />
      </div>
    </div>
  );
}

function getDisabledReason(user: AdminUserDetail) {
  if (user.del_yn) return "탈퇴 사용자는 변경할 수 없습니다.";
  if (user.is_self) return "본인 계정은 보호됩니다.";
  return null;
}
