# 해독 AI — Client

> **[필수] 이 디렉토리의 코드를 작성/수정/디버깅하기 전에 반드시 `/remix-dev` skill을 실행하세요.** <br/>
> skill을 실행하지 않고 코드를 작성하면 프로젝트 컨벤션을 위반할 수 있습니다.

## 연동 정보

- **Backend:** apps/server/ (FastAPI REST API)
- **인증:** Google/Kakao OAuth, JWT httpOnly 쿠키, Refresh Token Rotation

---

## 기술 스택

> 핵심 기술 스택은 루트 CLAUDE.md 참조. 아래는 client 고유 정보만.

- **Framework:** React Router v7 (framework mode) — *Remix는 v7부터 React Router에 통합됨*
- **언어:** TypeScript
- **스타일링:** Tailwind CSS + shadcn/ui
- **상태 관리:** Zustand (클라이언트), loader/action (서버 데이터)
- **폼:** React Hook Form + Zod

---

## 프로젝트 구조 (FSD 기반)

```
apps/client/app/
├── routes/           # Remix 파일 기반 라우팅 (loader + action + UI 위임)
├── views/            # 페이지 뷰 컴포넌트
├── widgets/          # 조합 UI (Header, Footer, Layout 등)
├── features/         # 기능별 모듈 (비즈니스 로직)
├── entities/         # 공유 도메인 모델 (post, translation, user)
└── shared/           # 공통 모듈 (api, types, stores, hooks, ui, lib, config)
```

> 상세 구조, Feature 모듈 패턴, loader/action 패턴은 `/remix-dev` skill 참조.

---

> **[필수] `/remix-dev` skill 포함 내용:** <br/>
> FSD 아키텍처, 구현 패턴 (Feature, Hook, View, loader/action), 코딩 컨벤션,
> API 컨벤션, CSS 클래스, 금지 규칙, 체크리스트

---

## 빌드 및 실행

```bash
npm run dev       # 개발 서버
npm run build     # 빌드
npm start         # 프로덕션 실행
npm run lint      # ESLint
npm run typecheck # TypeScript 타입 체크
```

---

## 환경 변수

> `.env` 참조. API Base URL, OAuth 설정 등.
