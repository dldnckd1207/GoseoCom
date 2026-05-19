import { CheckCircle, HelpCircle, XCircle } from 'lucide-react';

import { closeModal, useModalStore } from '~/shared/stores/modalStore';
import { Button } from '~/shared/ui/button';
import {
    Dialog,
    DialogContent,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from '~/shared/ui/dialog';

import type { ModalButton, ModalType } from '~/shared/stores/modalStore';

const TYPE_CONFIG: Record<ModalType, { title: string; icon: React.ReactNode }> = {
    alert: {
        title: '알림',
        icon: <CheckCircle className="w-5 h-5 text-green-600" aria-hidden />,
    },
    confirm: {
        title: '확인',
        icon: <HelpCircle className="w-5 h-5 text-blue-600" aria-hidden />,
    },
    error: {
        title: '오류',
        icon: <XCircle className="w-5 h-5 text-red-600" aria-hidden />,
    },
};

const DEFAULT_BUTTON: ModalButton = { label: '확인' };

export function Modal() {
    const { modal } = useModalStore();

    if (!modal) return null;

    const { type, message, title, buttons, dismissible = true, showIcon = true } = modal;
    const { title: defaultTitle, icon } = TYPE_CONFIG[type];
    const resolvedButtons = buttons ?? [DEFAULT_BUTTON];

    // modal 상태가 있을 때만 렌더링되므로 open은 항상 true
    return (
        <Dialog
            open
            onOpenChange={(open) => {
                if (!open && !dismissible) return;
                if (!open) closeModal();
            }}
        >
            <DialogContent showCloseButton={false}>
                <DialogHeader>
                    <DialogTitle>
                        <span className="flex items-center gap-2">
                            {showIcon && icon}
                            {title ?? defaultTitle}
                        </span>
                    </DialogTitle>
                </DialogHeader>
                <p className="text-sm text-muted-foreground max-h-40 overflow-y-auto whitespace-pre-line">{message}</p>
                <DialogFooter>
                    {resolvedButtons.map((btn, idx) => (
                        <Button
                            key={`${btn.label}-${idx}`}
                            variant={btn.variant ?? 'default'}
                            onClick={() => {
                                btn.onClick?.();
                                closeModal();
                            }}
                        >
                            {btn.label}
                        </Button>
                    ))}
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
