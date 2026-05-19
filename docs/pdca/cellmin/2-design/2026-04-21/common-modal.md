# Design — 공통 모달 컴포넌트

**Feature:** common-modal  
**Author:** cellmin  
**Date:** 2026-04-21  
**Redmine:** #102  
**Plan:** docs/pdca/cellmin/1-plan/2026-04-21/common-modal.md

---

## 1. 아키텍처

Zustand `modalStore`가 전역 모달 상태를 관리한다.
`root.tsx`의 `App()`에 `<Modal />`을 마운트해 어디서든 `openModal()`만 호출하면 렌더링된다.
shadcn/ui `Dialog`를 기반으로 구현하여 접근성(a11y)과 애니메이션을 기본 확보한다.

```
hook / View
    ↓ openModal(config)
modalStore (Zustand)
    ↓ modal 상태 변경
Modal.tsx (root.tsx에 마운트)
    ↓ Dialog 렌더링
```

---

## 2. 코드 구조

```
apps/client/app/
├── shared/
│   ├── stores/
│   │   └── modalStore.ts        # Zustand — modal 상태 + openModal/closeModal
│   └── ui/
│       └── modal/
│           ├── Modal.tsx         # 모달 컴포넌트
│           └── index.ts          # 배럴 export
└── root.tsx                      # App()에 <Modal /> 전역 마운트 (수정)
```

---

## 3. 타입 정의

```ts
// shared/stores/modalStore.ts (타입 포함)

export type ModalType = 'alert' | 'confirm' | 'error';

export type ModalButton = {
    label: string;
    // shadcn Button variant와 일치 ('primary' 없음 → 'default' 사용)
    variant?: 'default' | 'destructive' | 'outline' | 'ghost' | 'secondary' | 'link';
    onClick?: () => void;   // 없으면 closeModal만 호출
};

export type ModalConfig = {
    type: ModalType;
    message: string;
    title?: string;          // 생략 시 type별 기본 제목 사용
    buttons?: ModalButton[]; // 생략 시 { label: '확인' } 1개 기본값
    dismissible?: boolean;   // false면 ESC/배경 클릭으로 닫힘 방지 (confirm 등에 활용)
};
```

---

## 4. shared/stores/modalStore.ts

```ts
import { create } from 'zustand';

type ModalStore = {
    modal: ModalConfig | null;
    openModal: (config: ModalConfig) => void;
    closeModal: () => void;
};

const useModalStore = create<ModalStore>((set) => ({
    modal: null,
    openModal: (config) => set({ modal: config }),
    closeModal: () => set({ modal: null }),
}));

export { useModalStore };

// 컴포넌트 외부(hook 등)에서 바로 호출 가능하도록 getState() 기반 별도 export
// ※ 클라이언트 전용 — SSR loader/action에서 직접 호출 금지
export const openModal = (config: ModalConfig) =>
    useModalStore.getState().openModal(config);

export const closeModal = () =>
    useModalStore.getState().closeModal();
```

---

## 5. shared/ui/modal/Modal.tsx

### type별 스타일

| type | 기본 제목 | 아이콘 (lucide) | 아이콘 색상 |
|------|---------|----------------|------------|
| `alert` | 알림 | CheckCircle | text-green-600 |
| `confirm` | 확인 | HelpCircle | text-blue-600 |
| `error` | 오류 | XCircle | text-red-600 |

### 버튼 variant — shadcn/ui Button variant와 동일

`default` | `destructive` | `outline` | `ghost` | `secondary` | `link`

### dismissible 동작

| dismissible | ESC/배경 클릭 |
|-------------|-------------|
| `true` (기본값) | 모달 닫힘 |
| `false` | 차단 (confirm 등에 활용) |

> **중첩 모달 미지원:** 단일 modal 상태만 관리. 모달 위에 모달 호출 시 기존 모달 교체됨.

### 구조 (pseudo-code)

```tsx
export function Modal() {
    const { modal, closeModal } = useModalStore();

    const buttons = modal?.buttons ?? [{ label: '확인' }];
    const dismissible = modal?.dismissible ?? true;

    return (
        <Dialog
            open={modal !== null}
            onOpenChange={(open) => {
                if (!open && !dismissible) return;  // confirm 등 실수 닫힘 방지
                if (!open) closeModal();
            }}
        >
            <DialogContent>
                <DialogHeader>
                    {/* type별 아이콘 + 기본 제목 */}
                </DialogHeader>
                <p>{modal?.message}</p>
                <DialogFooter>
                    {buttons.map((btn) => (
                        <Button
                            key={btn.label}
                            variant={btn.variant ?? 'default'}
                            onClick={() => { btn.onClick?.(); closeModal(); }}
                        >
                            {btn.label}
                        </Button>
                    ))}
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
```

---

## 6. shared/ui/modal/index.ts

```ts
export { Modal } from './Modal';
export { openModal, closeModal } from '~/shared/stores/modalStore';
export type { ModalConfig, ModalButton, ModalType } from '~/shared/stores/modalStore';
```

---

## 7. root.tsx 수정

```tsx
import { Modal } from '~/shared/ui/modal';

export default function App() {
    return (
        <>
            <Outlet />
            <Modal />
        </>
    );
}
```

---

## 8. FIXME 교체

### _layout.tsx (before)
```ts
alert('로그아웃 되었습니다.');
navigate('/', { replace: true });
```

### _layout.tsx (after)
```ts
openModal({
    type: 'alert',
    message: '로그아웃 되었습니다.',
    buttons: [{ label: '확인', onClick: () => navigate('/', { replace: true }) }],
});
```

### auth.logout.tsx
```ts
// FIXME 주석 제거
```

---

## 9. 의존성 추가

```bash
npx shadcn@latest init        # Tailwind v4 + React Router v7 기준
npx shadcn@latest add dialog button
```

---

## 10. 테스트 전략

- `npm run typecheck` 통과
- `npm run lint` 통과
- 수동 검증:
  - `openModal({ type: 'alert', message: '...' })` → 모달 렌더링 확인
  - 확인 버튼 클릭 → onClick 실행 + 모달 닫힘 확인
  - onClick 없는 버튼 → 모달 닫힘만 확인
  - 로그아웃 시 alert() 대신 모달 표시 확인
  - ESC 키 / 배경 클릭 → alert/error 모달 닫힘, dismissible:false 모달은 차단 확인
