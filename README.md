# Haedok AI (解讀 AI)

고서(한문/한글 고문서) 이미지를 OCR과 AI로 자동 번역하고, 커뮤니티에서 함께 토론하는 플랫폼

---

## Overview

Haedok AI는 고서 이미지를 업로드하면 자동으로 텍스트를 추출하고, AI를 통해 직역과 의역을 제공합니다. 커뮤니티 게시판에서 고서 관련 질문과 토론이 가능하며, AI가 자동으로 답변을 생성하여 응답 공백을 줄입니다.

### Key Features

- **OCR 텍스트 추출** - 고서 이미지에서 한자/한글 자동 인식
- **AI 직역/의역** - 원문의 직역과 의역을 분리하여 제공, 사용자 수정 가능
- **커뮤니티 게시판** - 고서 관련 질문, 토론, 지식 공유
- **AI 자동 댓글** - OCR 파이프라인 결과를 자동 댓글로 등록
- **AI 자동 답변** - 일정 시간 내 답글이 없으면 AI가 자동으로 답변 생성

---

## Tech Stack

| 영역 | 기술 |
|------|------|
| Client (사용자) | React Router v7 (framework mode, ex-Remix) + TypeScript + Tailwind CSS |
| Admin | React + Vite + TypeScript + Tailwind CSS + TanStack Query |
| Backend | FastAPI (Python 3.12+) + SQLAlchemy 2.x (async) + Alembic |
| Database | PostgreSQL 16+ |
| OCR | PaddleOCR / Google Vision API |
| AI Model | Gemini Flash / Claude Haiku |
| Deployment | Docker Compose + nginx |

---

## Getting Started

### Prerequisites

- Python 3.12+
- Node.js LTS
- Docker & Docker Compose
- PostgreSQL 16+

### 로컬 개발 환경

```bash
git clone https://github.com/<org>/haedok-ai.git
cd haedok-ai

# pre-commit 훅 설치
pre-commit install   # 또는: uv tool install pre-commit && pre-commit install

# 서버 (FastAPI)
cd apps/server
cp .env.example .env   # DB, JWT, OAuth, API 키 등 값 채우기
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload

# 클라이언트 (Remix SSR)
cd ../client
npm install
npm run dev
```

### Environment Variables

환경 변수는 `apps/server/.env.example`를 참조하세요. 주요 항목:

- **Postgres**: `POSTGRES_HOST/PORT/DB/USER/PASSWORD`
- **앱**: `APP_SECRET_KEY`, `APP_CORS_ORIGINS`
- **JWT**: `JWT_SECRET_KEY`, `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`
- **OAuth**: `GOOGLE_CLIENT_ID/SECRET`, `KAKAO_CLIENT_ID/SECRET`
- **OCR**: `OCR_ENGINE`, `GOOGLE_VISION_API_KEY`
- **번역**: `TRANSLATOR_ENGINE`, `GEMINI_API_KEY`, `ANTHROPIC_API_KEY`

---

### 배포 (Docker)

PostgreSQL은 별도 운영하며, server + client만 Docker Compose로 관리합니다.

```bash
# 환경 변수 설정
cp apps/server/.env.example apps/server/.env   # DB, JWT, OAuth, API 키 등
cp apps/client/.env.example apps/client/.env

# 전체 배포 (빌드 → 마이그레이션 → 기동)
cd docker && ./deploy.sh
```

상세 내용은 [`docker/README.md`](docker/README.md)를 참조하세요.

---

## Project Structure

```
haedok-ai/
├── apps/
│   ├── client/        # Remix (사용자 웹)        — CLAUDE.md
│   ├── server/        # FastAPI 백엔드           — CLAUDE.md
│   └── admin/         # React + Vite (관리자)    — CLAUDE.md
├── docs/              # 프로젝트 문서 (PRD, SRS 등)
├── docker/            # docker-compose, nginx, postgres init
└── README.md
```

각 앱 디렉토리의 `CLAUDE.md`에 컨벤션과 진입점이 정의되어 있습니다.

---

## 개발 가이드 (Claude Code Skills)

본 프로젝트는 Claude Code skill을 통해 컨벤션을 강제합니다.
**해당 디렉토리의 코드를 작성/수정/디버깅하기 전에 반드시 매칭되는 skill을 실행하세요.**

| 디렉토리 | Skill | 범위 |
|----------|-------|------|
| `apps/server/` | `/server-dev` | FastAPI, SQLAlchemy, 도메인/레이어 구조, API 컨벤션 |
| `apps/client/` | `/remix-dev` | React Router v7 (framework mode, ex-Remix), FSD, loader/action 패턴 |
| `apps/admin/`  | `/react-dev` | React + Vite, FSD, TanStack Query 패턴 |
| DB 작업 (테이블/컬럼/마이그레이션) | `/db-dev` | 명명 규칙, ID 전략, 공통 컬럼, Alembic 규칙 |

> Skill 없이 작성하면 프로젝트 컨벤션을 위반할 수 있습니다.

---

## Team

| 역할 | 담당 |
|------|------|
| Frontend | React / Remix 게시판 UI, OCR 결과 표시/편집 |
| Backend | FastAPI API, DB 설계, 스케줄러 |
| AI Pipeline | PaddleOCR 연동, AI 번역, 자동 댓글/답변 |

---

## Roadmap

- [x] PRD / SRS / Architecture / Domain / ERD 작성
- [x] 프로젝트 계획서 작성
- [x] FastAPI 서버 초기 구조 + Alembic 마이그레이션
- [x] OAuth 인증 (Google / Kakao)
- [x] 게시판 관리 (다중 게시판 CRUD)
- [x] 게시글 / 댓글 CRUD + 파일 업로드/서빙
- [x] Docker 배포 구성 (server + client)
- [ ] **Phase 1 진행 중** — 고서 번역기(OCR + AI), 라이브러리, AI 자동 답변
- [ ] **Phase 2** — 번역 수정, 요약/키워드, 결과 저장/공유
- [ ] **Phase 3** — 관리자 페이지, 악성댓글 필터링, 회원 시스템

---

## Documents

### Specs
- [PRD](docs/specs/01_PRD.md) — Product Requirements Document
- [SRS](docs/specs/02_SRS.md) — Software Requirements Specification
- [Architecture](docs/specs/03_Architecture.md) — 시스템 아키텍처
- [Domain](docs/specs/04_Domain.md) — 도메인 모델
- [ERD](docs/specs/05_ERD.md) — DB 스키마

### Reports & Designs
- [프로젝트 계획서](docs/reports/프로젝트_계획서_v2.0.md)
- [시스템 아키텍처 다이어그램](docs/reports/시스템_아키텍처.svg)
- `docs/sdd/` — Phase별 상세 설계 (SDD)
- `docs/designs/` — UI/UX 디자인
- `docs/meetings/` — 회의록

---

## License

[LICENSE](LICENSE)
