# Plan — 번역 페이지 구현 + 보호 Route 기반 구축

**Feature:** translate-page  
**Author:** cellmin  
**Date:** 2026-04-22  
**Redmine:** #97  

---

## 1. 목표

번역 페이지(`/translate`)를 구현하고, 로그인 필수 페이지들을 위한 `_protected.tsx` 레이아웃을 구축한다.
번역 기능 자체는 백엔드 미완성으로 "서비스 준비중" 모달로 대체하고,
미로그인 접근 시 로그인 후 원래 URL로 자동 복귀하는 흐름도 함께 구현한다.

---

## 2. 배경

- `_protected.tsx`는 typegen 버그로 이전에 보류 → 이번에 실제 하위 route(`/translate`)와 함께 구현
- 번역, 라이브러리, 커뮤니티 글작성은 로그인 사용자만 접근 가능
- 백엔드 번역 파이프라인 미완성 → "서비스 준비중" 모달로 UX 처리
- OAuth 특성상 로그인 후 URL 복귀는 sessionStorage 기반으로 클라이언트 단에서 처리

---

## 3. 핵심 요구사항

### 3-1. `_protected.tsx` 레이아웃
- SSR loader에서 `/me` 호출 → 401이면 현재 경로를 sessionStorage에 저장 후 `/login` redirect
- 로그인 상태면 Header + Footer + user 정보 포함하여 렌더링
- 향후 `/library`, `/community/write` 등도 이 레이아웃 사용

### 3-2. 로그인 후 URL 복귀 (sessionStorage redirect)
- `_protected.tsx` loader에서 미인증 시 `sessionStorage.setItem('redirectAfterLogin', pathname)` 저장
  - 단, loader는 SSR이므로 sessionStorage 직접 접근 불가 → redirect URL을 `/login?redirect=/translate` 형태로 전달
  - `_auth.login.tsx` 또는 `root.tsx`에서 OAuth 완료 후 sessionStorage 확인 후 navigate
- OAuth 완료 → `/` 도달 → `root.tsx`에서 `?redirect=` 쿼리 또는 sessionStorage 확인 → 자동 이동

### 3-3. `/translate` 페이지 UI
`docs/designs/client/translate.html` 목업 기반:
- 파일 업로드 영역 (드래그앤드롭 UI, 실제 업로드 미구현)
- 원본 텍스트 입력 textarea
- "AI 번역 시작" 버튼 → 클릭 시 `openModal({ type: 'alert', message: '서비스 준비 중입니다.' })`
- 번역 결과 영역 (빈 상태 표시)
- 사용 안내 섹션

---

## 4. 로그인 후 URL 복귀 흐름

```
1. 미로그인 사용자 /translate 접근
2. _protected.tsx loader → redirect('/login?redirect=/translate')
3. LoginView에서 OAuth 버튼 href에 redirect 파라미터 포함
   → /auth/kakao?redirect=/translate (서버에서 무시해도 됨, 클라이언트 저장용)
4. 실제로는: 버튼 클릭 시 sessionStorage.setItem('redirectAfterLogin', '/translate') 저장 후 OAuth 이동
5. OAuth 완료 → / 도착
6. root.tsx 또는 _layout.tsx의 useEffect에서 sessionStorage 확인
7. redirectAfterLogin 있으면 navigate(path) 후 sessionStorage 삭제
```

> **핵심:** sessionStorage에 저장 → OAuth → 돌아온 후 읽어서 이동. 서버 변경 불필요.

---

## 5. 범위 외 (Out of Scope)

- 실제 파일 업로드 및 OCR 처리
- 실제 AI 번역 API 연동
- 번역 결과 다운로드 기능
- 번역 이력 저장

---

## 6. 성공 기준

- [ ] 미로그인 상태에서 `/translate` 접근 시 `/login?redirect=/translate`으로 redirect
- [ ] 로그인 완료 후 `/translate`로 자동 복귀
- [ ] `/translate` 페이지 렌더링 (목업 기반 UI)
- [ ] "AI 번역 시작" 클릭 시 "서비스 준비 중입니다." 모달 표시
- [ ] `npm run typecheck` 통과
- [ ] `npm run lint` 통과

---

## 7. 기술 스택

- React Router v7 (framework mode), TypeScript, Tailwind CSS v4
- Zustand modalStore (`openModal`)
- sessionStorage (로그인 후 URL 복귀)
- remix-dev skill 컨벤션 준수 (FSD, flat routes, `~/*` alias)
