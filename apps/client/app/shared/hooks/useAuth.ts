import { useAuthStore } from '~/shared/stores/authStore';

export function useAuth() {
    const user = useAuthStore((s) => s.user);
    return {
        user,
        isLoggedIn: user !== null,
    };
}
