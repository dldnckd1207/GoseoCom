import { create } from "zustand";

export type ModalType = "alert" | "confirm" | "error";

export interface ModalButton {
  label: string;
  variant?: "default" | "destructive" | "outline" | "ghost" | "secondary";
  onClick?: () => void;
}

export interface ModalConfig {
  type: ModalType;
  message: string;
  title?: string;
  buttons?: ModalButton[];
  dismissible?: boolean;
}

interface ModalStore {
  modal: ModalConfig | null;
  openModal: (config: ModalConfig) => void;
  closeModal: () => void;
}

export const useModalStore = create<ModalStore>((set) => ({
  modal: null,
  openModal: (config) => set({ modal: config }),
  closeModal: () => set({ modal: null }),
}));

export const openModal = (config: ModalConfig) => useModalStore.getState().openModal(config);

export const closeModal = () => useModalStore.getState().closeModal();
