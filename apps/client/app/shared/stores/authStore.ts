import { create } from 'zustand';

import type { User } from '~/shared/types/auth';

type AuthStore = {
    user: User | null;
    setUser: (user: User | null) => void;
    clear: () => void;
};

export const useAuthStore = create<AuthStore>((set) => ({
    user: null,
    setUser: (user) => set({ user }),
    clear: () => set({ user: null }),
}));
