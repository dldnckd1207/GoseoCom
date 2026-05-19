# Plan — community-api-connect

> **Redmine:** #104 · **날짜:** 2026-05-04 · **작업자:** cellmin

---

## 1. 목표

커뮤니티(게시판) 화면(`/community`, `/community/:id`, `/community/write`)의
Mock 데이터를 제거하고 실제 백엔드 REST API로 교체한다.

## 2. 배경

| SFR | 기능 | BE 상태 |
|-----|------|---------|
| SFR-105 | 게시판 관리 (다중 게시판) | ✅ 완료 |
| SFR-101 | 게시글 + 댓글 CRUD + 파일 업로드 | ✅ 완료 |

이전 PDCA 사이클에서 community-list, community-detail 화면 자체는 완료됐으나
Mock 데이터 상태로 남아 있음. 이번 작업에서 실제 API 연결을 완성한다.

## 3. 확인된 사항 (리뷰 + 분석 결과)

| 항목 | 내용 |
|------|------|
| 게시판 비회원 읽기 | 3개 게시판 모두 `guest_read_yn = true` → 비로그인도 전체 조회 가능 |
| 탭 구성 방식 | 하드코딩 → **boards API 동적 조회**로 변경 |
| 게시판 구분 컬럼 | BE `cms_tn_board`에 `board_group: str | None` 추가 (`'community'` 등) |
| all 탭 정책 | board_codes 리스트를 한 번에 전달 → BE `IN` 쿼리로 단일 조회 |
| 게시글 작성 | 이번 범위 포함 (write 페이지 API 연결까지) |

## 4. 작업 범위

### BE 추가 작업

- `cms_tn_board` 테이블에 `board_group` 컬럼 추가 (Alembic 마이그레이션)
- Seed 데이터 업데이트: 3개 게시판 `board_group = 'community'`
- `BoardListRequest`에 `board_group` 필터 추가
- `BoardSummaryResponse`에 `board_group` 필드 추가
- `PostListRequest.board_code: str` → `board_codes: list[str]` 변경
- `PostRepository.list()`에 `board_ids: list[str]` + `IN` 쿼리 적용

### FE 작업

- `shared/api/endpoints.ts` — boards, posts, comments 엔드포인트 추가
- `shared/types/post.ts` — BE API 응답 타입 추가 (`PostSummary`, `PostDetail`, `CommentItem`, `BoardSummary`)
- `views/community/config.ts` — 하드코딩 config 제거, 동적 boards 데이터 사용
- `routes/_layout.community._index.tsx` — loader에서 boards/list + posts/list 연결
- `views/community/CommunityListView.tsx` — Mock 제거, loader 데이터 기반 동적 탭 렌더링
- `routes/_layout.community.$id.tsx` — posts/{id} + comments/list + comment action
- `views/community/CommunityDetailView.tsx` — 새 타입 적용, useFetcher 댓글 작성
- `routes/_layout.community.write.tsx` — 게시글 작성 폼 + API 연결

## 5. 요구사항

### 기능 요구사항

| ID | 요구사항 | 우선순위 |
|----|---------|---------|
| FR-1 | 게시판 목록을 API에서 동적으로 조회해 탭 렌더링 | 필수 |
| FR-2 | 게시글 목록을 BE API에서 로드 (board_codes 리스트 전달) | 필수 |
| FR-3 | all 탭은 커뮤니티 게시판 전체를 단일 API 호출로 조회 | 필수 |
| FR-4 | 비로그인 포함 전체 게시판 목록/상세 조회 가능 | 필수 |
| FR-5 | 게시글 단건 조회 시 실제 BE API 호출 | 필수 |
| FR-6 | 댓글 목록을 BE API에서 로드 | 필수 |
| FR-7 | 로그인 사용자가 댓글 작성 가능, 작성 후 목록 자동 갱신 | 필수 |
| FR-8 | 로그인 사용자가 게시글 작성 가능 | 필수 |

### 비기능 요구사항

- Mock 파일(mock.ts, mockComments.ts)은 삭제하지 않고 import만 제거
- 게시판 탭은 `board_group = 'community'` 게시판만 표시
- 게시판이 추가되어도 FE 코드 변경 없이 자동 반영

### 에러 처리 기준

| 상황 | 처리 |
|------|------|
| 게시글 404 | 라우트 에러 경계 → Not Found |
| 댓글 작성 401/403 | action에서 catch → 폼 하단 에러 메시지 표시 |
| 목록 API 실패 | 빈 목록 + 에러 메시지 표시 |
| 게시글 작성 실패 | 폼 하단 에러 메시지 표시 |

## 6. 성공 기준

- [ ] `/community` 접속 시 boards API에서 동적으로 탭 구성
- [ ] 게시글 목록이 실제 DB 데이터로 표시
- [ ] all 탭: 단일 API 호출로 전체 게시판 게시글 표시
- [ ] 비로그인 사용자도 전체 탭/목록 조회 가능
- [ ] `/community/:id` 접속 시 실제 게시글 상세 + 댓글 표시
- [ ] 댓글 작성 성공 → 목록 자동 갱신, 입력창 초기화
- [ ] 댓글 작성 실패 → 에러 메시지 표시
- [ ] `/community/write` 게시글 작성 후 상세 페이지로 이동
- [ ] TypeScript 타입 체크 통과
