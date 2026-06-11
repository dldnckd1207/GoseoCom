import { AlertTriangle, CheckCircle2, HelpCircle } from "lucide-react";

import { closeModal, useModalStore } from "~/shared/stores/modalStore";
import { Button } from "~/shared/ui/button";

const typeTitle = {
  alert: "알림",
  confirm: "확인",
  error: "오류",
} as const;

const typeIcon = {
  alert: <CheckCircle2 className="size-5 text-[#a0c3ec]" />,
  confirm: <HelpCircle className="size-5 text-[#c4b5fd]" />,
  error: <AlertTriangle className="size-5 text-destructive" />,
} as const;

export function Modal() {
  const { modal } = useModalStore();

  if (!modal) return null;

  const buttons = modal.buttons ?? [{ label: "확인" }];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 px-4">
      <div className="w-full max-w-sm rounded-md border border-border bg-popover p-5 text-popover-foreground">
        <div className="flex items-center gap-2">
          {typeIcon[modal.type]}
          <h2 className="text-base font-medium">{modal.title ?? typeTitle[modal.type]}</h2>
        </div>
        <p className="mt-4 whitespace-pre-line text-sm leading-6 text-muted-foreground">
          {modal.message}
        </p>
        <div className="mt-5 flex justify-end gap-2">
          {buttons.map((button) => (
            <Button
              key={button.label}
              variant={button.variant}
              onClick={() => {
                button.onClick?.();
                closeModal();
              }}
            >
              {button.label}
            </Button>
          ))}
        </div>
      </div>
    </div>
  );
}
