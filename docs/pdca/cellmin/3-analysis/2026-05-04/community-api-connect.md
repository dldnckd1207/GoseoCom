# Check Analysis — community-api-connect

> **Redmine:** #104 · **날짜:** 2026-05-04 · **작업자:** cellmin
> **검토 에이전트:** FE 리뷰어 + BE 리뷰어 (병렬 실행) + 사용자 추가 지적

---

## 영역별 점수

| 영역 | 비중 | 점수 | 수정 전 | 수정 후 |
|------|------|------|---------|---------|
| 기능 완성도 | 20% | 90 | 88 | 90 |
| 코드 품질 | 20% | 80 | 62 | 80 |
| 테스트 | 20% | 72 | 60 | 72 |
| 보안 | 20% | 82 | 60 | 82 |
| 성능 | 10% | 78 | 72 | 78 |
| 문서화 | 10% | 75 | 70 | 75 |

**종합 점수: 81 / 100** (수정 전 68)

---

## 이번 사이클에서 수정 완료한 항목

### [High] 수정 완료

| # | 이슈 | 수정 내용 |
|---|------|-----------|
| H-1 | `list_posts` `board_ids=[]` 빈 IN 쿼리 → 500 | early return PageData(items=[]) 추가 |
| H-2 | `list_posts` 비community 게시판 권한 검증 누락 | `board_group is None` 게시판에 `_check_read_permission` 적용 |
| H-3 | `write.tsx` FSD 위반 (UI가 route에 직접 구현) | `CommunityWriteView` 분리 |
| H-4 | `PageResult<T>` 3개 파일 중복 선언 | `shared/types/post.ts`로 단일화 |
| H-5 | `formatDate` 2개 View 중복 정의 | `shared/lib/date.ts`로 추출 |
| H-6 | 테스트 `board_code` → `board_codes` API 계약 미반영 | `test_post.py` 수정 + 404→200 empty 기대값 변경 |
| H-7 | `board_group` 인덱스 누락 | 마이그레이션 + `models.py` `__table_args__` 추가 |
| H-8 | `AdminBoardCreateRequest/UpdateRequest`에 `board_group` 없음 | 양쪽 스키마에 `board_group` 필드 추가 |

### [Medium] 수정 완료

| # | 이슈 | 수정 내용 |
|---|------|-----------|
| M-1 | `write.tsx` react-router 이중 import | 단일 import 구문으로 통합 |
| M-2 | `author_name: string \| null` null 처리 없음 | `{c.author_name ?? '익명'}` 적용 |
| M-3 | 댓글 수 `comments.length` → `post.comment_count` | 수정 완료 |
| M-4 | `CommunityListView` 불필요 `useEffect` (URL 정규화) | 삭제 (loader가 이미 effectiveTab 정규화) |

---

## 잔여 이슈 (Act 단계 대상)

### Medium

| # | 파일 | 이슈 |
|---|------|------|
| M-R1 | `_index.tsx`, `$id.tsx` | `boardsData`, `postsData` fetch에 try/catch 없어 BE 장애 시 500 노출 |
| M-R2 | `$id.tsx` | 404 케이스 미처리 (post not found 시 빈 화면) |
| M-R3 | `server.ts` | SSR 401 시 token refresh 없이 ApiError로 throw — ME 이외 API도 영향 가능 |
| M-R4 | `post_service.py` | `_validate_files` N+1 쿼리 (파일 첨부 시) |
| M-R5 | `post_service.py` | `update_post` 파일 응답 로직 중복, 경로가 복잡해 회귀 위험 |

### Low

| # | 파일 | 이슈 |
|---|------|------|
| L-1 | `CommunityListView.tsx` | 페이지네이션 전체 페이지 버튼 렌더링 (대용량 시 UI 깨짐) |
| L-2 | `shared/types/post.ts` | `PostDetail.files: unknown[]` 타입 미정의 |
| L-3 | `shared/types/post.ts` | 레거시 `Post`, `Comment`, `PostTab`, `PostEra` 타입 잔존 |
| L-4 | `post_schemas.py` | `keyword examples=[None]` 대신 실제 예시 값 권장 |
| L-5 | `repository.py` | `has_posts()` `select_from(Post)` 명시 권장 |

---

## 컨벤션 준수 현황

### remix-dev (FSD + React Router v7)

| 항목 | 상태 |
|------|------|
| routes/에 loader/action만, UI는 views로 위임 | ✅ (write.tsx 분리 완료) |
| views/에서 직접 API 호출 없음 | ✅ |
| `useLoaderData()` / `useFetcher()` 패턴 | ✅ |
| 서버 데이터는 loader → `useLoaderData()` | ✅ |
| 뮤테이션은 action + Form 또는 useFetcher | ✅ |
| import 순서 (react-router → 외부 → 내부 → type) | ✅ |
| shared/types에 도메인 타입 위치 | ✅ |
| 불필요 useState/useEffect 없음 | ✅ (정규화 useEffect 제거) |

### server-dev (FastAPI + SQLAlchemy)

| 항목 | 상태 |
|------|------|
| Router → Service → Repository 흐름 | ✅ |
| Service에서 commit(), Repository에서 flush() | ✅ |
| `require_level` Dependency 적용 | ✅ |
| Pydantic `Field(..., description, examples)` | ✅ |
| `model_config = {"from_attributes": True}` | ✅ |
| 빈 IN 쿼리 방어 | ✅ (early return 추가) |
| board_group 인덱스 | ✅ (마이그레이션 + 모델 추가) |
| 권한 검증 일관성 (list/detail) | ✅ (community 정책 반영) |

---

## 2차 Check (Act 이후) — 최종 점수

| 영역 | 점수 |
|------|------|
| 기능 완성도 | 90 |
| 코드 품질 | 88 |
| 테스트 | 88 |
| 보안 | 93 |
| 성능 | 95 |
| 문서화 | 85 |

**종합 점수: 90 / 100** — 품질 목표 달성

### 2차에서 추가 수정한 항목

- `AdminBoardResponse`에 `board_group` 필드 추가
- `write.tsx` 미사용 import 5개 제거
- `list_posts` API description → board_group 정책 반영
- `fetchError` → `boardsError` / `postsError` 분리, `??`로 우선순위 결합

### 잔여 Low 이슈 (다음 이슈로 관리)

- 탭 버튼 `aria-selected` / `role="tab"` 접근성
- 목록에 조회수/댓글수 컬럼 추가 (UX 개선)
- 레거시 타입(`Post`, `Comment`) 정리 (mock 파일 정리 시 함께)
- SSR 401 refresh 처리 (`serverFetch` 인프라 전체 이슈)
