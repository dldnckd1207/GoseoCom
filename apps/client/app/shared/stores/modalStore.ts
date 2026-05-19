import { create } from 'zustand';

export type ModalType = 'alert' | 'confirm' | 'error';

export type ModalButton = {
    label: string;
    variant?: 'default' | 'destructive' | 'outline' | 'ghost' | 'secondary' | 'link';
    onClick?: () => void;
};

export type ModalConfig = {
    type: ModalType;
    /** 본문 메시지 */
    message: string;
    /** 생략 시 type별 기본 제목 사용 (알림 / 확인 / 오류) */
    title?: string;
    /** 생략 시 '확인' 버튼 1개 기본값. 최대 3개 */
    buttons?: ModalButton[];
    /** false면 ESC·배경 클릭으로 닫힘 방지. 기본값 true */
    dismissible?: boolean;
    /** false면 제목 앞 아이콘 숨김. 기본값 true */
    showIcon?: boolean;
};

type ModalStore = {
    modal: ModalConfig | null;
    openModal: (config: ModalConfig) => void;
    closeModal: () => void;
};

export const useModalStore = create<ModalStore>((set) => ({
    modal: null,
    openModal: (config) => set({ modal: config }),
    closeModal: () => set({ modal: null }),
}));

/**
 * 모달을 열어 메시지와 버튼을 표시한다.
 * buttons 생략 시 '확인' 버튼 1개가 기본 적용된다.
 * ※ 클라이언트 전용 — SSR loader/action에서 직접 호출 금지
 */
export const openModal = (config: ModalConfig) =>
    useModalStore.getState().openModal(config);

/** 현재 열린 모달을 닫는다. */
export const closeModal = () =>
    useModalStore.getState().closeModal();
