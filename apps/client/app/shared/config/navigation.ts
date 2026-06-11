export type NavItem = {
    path: string;
    label: string;
    minLevel: number;
};

export const NAV_LINKS = [
    { path: '/translate', label: '번역하기', minLevel: 0 },
    { path: '/translate-test', label: '학습하기 (Beta)', minLevel: 1 },
    { path: '/community', label: '커뮤니티', minLevel: 0 },
    { path: '/library',   label: '라이브러리', minLevel: 0 },
    { path: '/history',   label: '번역 이력',  minLevel: 1 },
] satisfies NavItem[];
