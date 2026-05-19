export type NavItem = {
    path: string;
    label: string;
    minLevel: number;
};

export const NAV_LINKS = [
    { path: '/translate', label: '번역하기', minLevel: 0 },
    { path: '/community', label: '커뮤니티', minLevel: 0 },
    { path: '/library',   label: '라이브러리', minLevel: 0 },
] satisfies NavItem[];
