# 해독 AI — Admin

> **[필수] 이 디렉토리의 코드를 작성/수정/디버깅하기 전에 반드시 `/react-dev` skill을 실행하세요.** <br/>
> skill을 실행하지 않고 코드를 작성하면 프로젝트 컨벤션을 위반할 수 있습니다.

## 연동 정보

- **Backend:** apps/server/ (FastAPI REST API)
- **API Base URL:** `/admin/api/**`
- **인증:** JWT httpOnly 쿠키

---

## 기술 스택

> 핵심 기술 스택은 루트 CLAUDE.md 참조. 아래는 admin 고유 정보만.

- **Framework:** React + Vite
- **언어:** TypeScript
- **스타일링:** Tailwind CSS + shadcn/ui
- **상태 관리 (서버):** TanStack Query
- **상태 관리 (클라이언트):** Zustand
- **폼:** React Hook Form + Zod
- **라우팅:** React Router

---

## 프로젝트 구조 (FSD 기반)

```
apps/admin/src/
├── app/              # 앱 설정 (providers, router)
├── pages/            # 라우트 페이지 (이벤트 핸들러만)
├── features/         # 기능별 모듈 (비즈니스 로직)
├── entities/         # 공유 도메인 모델
└── shared/           # 공통 모듈 (api, ui, hooks, lib, store)
```

> 상세 구조, Hook 패턴, QueryKeys, 코딩/API 컨벤션은 `/react-dev` skill 참조.

---

> **[필수] `/react-dev` skill 포함 내용:** <br/>
> FSD 패턴, Hook 종류 (List/Detail/Mutation/Form), TanStack Query 패턴,
> 코딩/API 컨벤션, CSS 유틸리티, 체크리스트

---

## 빌드 및 실행

```bash
npm run dev       # 개발 서버
npm run build     # 빌드
npm run preview   # 빌드 미리보기
npm run lint      # ESLint
npm run typecheck # TypeScript 타입 체크
```

---

## 환경 변수

> `.env.local` 참조. API Base URL, 환경 설정 등.
