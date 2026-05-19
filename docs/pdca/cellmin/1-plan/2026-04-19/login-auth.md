# Plan — 로그인 페이지 + Frontend Auth 관리

**Feature:** login-auth  
**Author:** cellmin  
**Date:** 2026-04-19  
**Redmine:** #96  

---

## 1. 목표

OAuth 소셜 로그인 화면을 구현하고, SSR 기반 Frontend 인증 상태 관리 전체를 구축한다.
이후 모든 페이지(번역, 커뮤니티, 고서 목록 등)의 보호 route와 메뉴 권한 제어의 기반이 된다.

---

## 2. 배경 및 컨텍스트

- 서버(FastAPI)에서 OAuth 인증 후 **httpOnly 쿠키**로 JWT 발급 (access_token 1시간, refresh_token 30일)
- JS에서 토큰 직접 접근 불가 → SSR loader에서 `/api/v1/users/me` 호출로 인증 여부 판단
- Refresh Token Rotation 방식 — 401 시 `/auth/refresh` 자동 재시도 필요
- 기존 `Header.tsx`는 NAV_ITEMS 하드코딩 → `shared/config/navigation.ts`로 이전

---

## 3. 핵심 요구사항

### 3-1. Auth 인프라
| 항목 | 내용 |
|------|------|
| fetch wrapper | 401 응답 시 `/auth/refresh` 자동 재시도 후 원래 요청 재전송 |
| authStore | Zustand — `/me` 응답(user_id, email, name, profile_image_url, user_level) 메모리 캐싱 |
| useAuth hook | 로그인 여부(`isLoggedIn`), 유저 정보(`user`) 접근 |
| navigation config | 메뉴 목록 + `minLevel` 권한 필드 — `shared/config/navigation.ts` |

### 3-2. Route 레이아웃 분기
| Route | 역할 |
|-------|------|
| `routes/_auth.tsx` | 비로그인 전용 레이아웃 — 로그인 상태면 `/` redirect |
| `routes/_protected.tsx` | 로그인 필수 레이아웃 — 미로그인이면 `/login` redirect |

### 3-3. 로그인 화면 (`/login`)
- Header/Footer 없는 중앙 카드 레이아웃
- 기존 사이트 스타일 유지 (흰 배경, blue-600 포인트, rounded-lg, shadow-sm)
- 소셜 로그인 버튼 2개
  - **카카오로 시작하기** — `/auth/kakao` 이동 (노란색 계열)
  - **Google로 시작하기** — `/auth/google` 이동 (흰 배경 + 테두리)
- 로고: 현재는 텍스트 버튼, 나중에 `public/icons/` 이미지로 교체 가능한 구조

### 3-4. Header 업데이트
- `navigation.ts` 기반 동적 렌더링
- `user_level >= minLevel` 조건으로 메뉴 필터링 (UX용)
- 로그인/비로그인 상태에 따라 우측 버튼 분기 (로그인 버튼 or 유저 아바타)

---

## 4. 인증 흐름

```
브라우저 요청
    ↓
React Router SSR loader
    ↓
GET /api/v1/users/me (httpOnly 쿠키 자동 포함)
    ↓
200 OK  →  authStore에 유저 정보 저장 → 페이지 렌더링
401     →  /auth/refresh 재시도
              ↓ 성공 → /me 재호출
              ↓ 실패 → /login redirect
```

---

## 5. 범위 외 (Out of Scope)

- 마이페이지, 회원탈퇴, 프로필 수정
- 소셜 로그인 공식 로고 이미지 (추후 교체 가능 구조만 확보)
- 관리자 메뉴 권한 (user_level 기반 구조만 잡음)

---

## 6. 성공 기준

- [ ] 로그인 상태에서 `/login` 접근 시 `/` redirect
- [ ] 미로그인 상태에서 보호 route 접근 시 `/login` redirect
- [ ] 카카오/Google 버튼 클릭 시 각 OAuth 엔드포인트로 이동
- [ ] OAuth 완료 후 Header에 유저 정보 반영
- [ ] `navigation.ts`에서 메뉴 추가/수정만으로 Header 변경 반영
- [ ] `npm run typecheck` 통과
- [ ] `npm run lint` 통과

---

## 7. 기술 스택

- React Router v7 (framework mode), TypeScript, Tailwind CSS v4
- Zustand (authStore)
- remix-dev skill 컨벤션 준수 (FSD, flat routes, `~/*` alias)
