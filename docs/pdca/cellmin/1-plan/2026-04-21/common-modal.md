# Plan — 공통 모달 컴포넌트

**Feature:** common-modal  
**Author:** cellmin  
**Date:** 2026-04-21  
**Redmine:** #102  

---

## 1. 목표

전역에서 재사용 가능한 공통 모달 컴포넌트를 구축한다.
현재 `alert()`로 임시 처리된 로그아웃 알림을 교체하고,
이후 커뮤니티/번역 등 전 페이지에서 알림·확인·오류 모달을 일관되게 사용할 수 있는 기반을 마련한다.

---

## 2. 배경

- `auth.logout.tsx`, `_layout.tsx` 두 곳에 `// FIXME: 공통 모달 개발 후 alert 대신 모달로 교체` 존재
- 커뮤니티 글 삭제, 폼 이탈 확인 등 향후 confirm 패턴이 다수 필요
- shadcn/ui 미설치 상태 → 이번 기회에 함께 도입

---

## 3. 모달 종류

| type | 아이콘 | 색상 | 용도 |
|------|--------|------|------|
| `alert` | ✓ CheckCircle | 초록(green-600) | 성공/완료 알림 |
| `confirm` | ? HelpCircle | 파랑(blue-600) | 사용자 확인 요청 |
| `error` | ✕ XCircle | 빨강(red-600) | 오류/경고 알림 |

---

## 4. 버튼 스펙

- 버튼 최대 3개
- 각 버튼에 `onClick` 콜백 직접 부착 (클로저로 컨텍스트 캡처)
- `onClick` 없으면 모달 닫기만 수행
- `buttons` 생략 시 `{ label: '확인' }` 1개 기본값 자동 적용

```ts
type ModalButton = {
    label: string;
    variant?: 'primary' | 'destructive' | 'outline' | 'ghost';
    onClick?: () => void;
};
```

---

## 5. 사용 패턴

```ts
// 단순 알림 (buttons 생략 → 확인 버튼 1개)
openModal({ type: 'alert', message: '로그아웃 되었습니다.' })

// 확인/취소
openModal({
    type: 'confirm',
    message: '글을 삭제하시겠습니까?',
    buttons: [
        { label: '삭제', variant: 'destructive', onClick: () => handleDelete(id) },
        { label: '취소', variant: 'outline' },
    ]
})

// 버튼 3개
openModal({
    type: 'confirm',
    message: '변경사항이 있습니다.',
    buttons: [
        { label: '저장', variant: 'primary', onClick: handleSave },
        { label: '저장 안함', variant: 'outline', onClick: handleDiscard },
        { label: '취소', variant: 'ghost' },
    ]
})

// 오류
openModal({ type: 'error', message: '권한이 없습니다.' })
```

---

## 6. 콜백 호출 위치

hook 안에서 `openModal` 호출. 비즈니스 로직(fetcher.submit 등)은 클로저로 캡처.

```ts
// features/community/hooks/usePostDetail.ts
const handleDelete = (postId: string) => {
    openModal({
        type: 'confirm',
        message: '글을 삭제하시겠습니까?',
        buttons: [
            { label: '삭제', variant: 'destructive',
              onClick: () => fetcher.submit({ intent: 'delete', id: postId }, { method: 'post' }) },
            { label: '취소', variant: 'outline' },
        ]
    });
};
```

---

## 7. 구현 범위

| 항목 | 내용 |
|------|------|
| shadcn/ui 설치 | Dialog, Button 컴포넌트 기반 |
| `shared/stores/modalStore.ts` | Zustand — openModal / closeModal / modal 상태 |
| `shared/ui/modal/Modal.tsx` | 모달 컴포넌트 (type별 아이콘/색상 분기) |
| `shared/ui/modal/index.ts` | 배럴 export |
| `root.tsx` | `<Modal />` 전역 마운트 |
| FIXME 교체 | `auth.logout.tsx`, `_layout.tsx` 2곳 |

---

## 8. 범위 외 (Out of Scope)

- 모달 내 폼 입력 (input, textarea 등)
- 중첩 모달
- 애니메이션 커스터마이징

---

## 9. 성공 기준

- [ ] `openModal({ type: 'alert', message: '...' })` 호출 시 모달 렌더링
- [ ] 버튼 클릭 시 onClick 실행 후 모달 자동 닫힘
- [ ] onClick 없는 버튼 클릭 시 모달 닫힘만
- [ ] 로그아웃 시 `alert()` 대신 모달로 "로그아웃 되었습니다." 표시
- [ ] FIXME 주석 2곳 제거
- [ ] `npm run typecheck` 통과
- [ ] `npm run lint` 통과

---

## 10. 기술 스택

- React Router v7 (framework mode), TypeScript, Tailwind CSS v4
- shadcn/ui (Dialog, Button)
- Zustand (modalStore)
- remix-dev skill 컨벤션 준수 (FSD, `~/*` alias)
