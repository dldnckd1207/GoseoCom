# Check: 커뮤니티 글 상세 페이지 (#99)

**평가일:** 2026-05-03
**평가자:** cellmin (PDCA Check)
**대상:** `_layout.community.$id.tsx`, `CommunityDetailView.tsx`, `config.ts`, `mock.ts`, `mockComments.ts`

---

## 성공 기준 달성 여부

| 기준 | 결과 |
|------|------|
| `/community/1` 게시글 상세 표시 | ✅ |
| `/community/11` 비로그인 → 접근 차단 화면 | ✅ |
| `/community/999` → 404 응답 + 에러 페이지 | ✅ |
| 댓글 목록 Mock 표시 | ✅ |
| 댓글 empty state "작성된 댓글이 없습니다." | ✅ |
| 댓글 작성 submit → preventDefault + 초기화 | ✅ |
| 비로그인 댓글 입력창 disabled + 안내 | ✅ |
| "목록으로" 링크 | ✅ |
| accessDenied 화면 "목록으로" + "로그인하기" | ✅ |
| 로그인 버튼 → `/login?redirect=/community/:id` | ✅ |
| meta title | ✅ |
| TypeScript 에러 없음 | ✅ |

---

## 영역별 평가

### 1. 기능 완성도 — 98 / 100

Plan의 모든 성공 기준 달성. `boardConfig`를 loader에서 반환하나 View에서 직접 사용하지 않음 (accessDenied로 파생 후 사용) — 소폭 감점.

### 2. 코드 품질 — 87 / 100

**양호:**
- Route → View 위임 패턴 준수 (`return <CommunityDetailView />`)
- View가 `useLoaderData` 직접 호출
- `config.ts` 분리 (Mock 데이터와 권한 정책 분리)
- FSD 레이어 의존성 규칙 준수
- Named export 원칙 준수 (route default export만 예외)
- Import 순서/그룹 준수

**개선 여지:**
- JSX 주석 `{/* 게시글 */}` `{/* 댓글 */}` `{/* 댓글 작성 */}` `{/* 댓글 목록 */}` — WHAT 설명형 주석 (컨벤션 위반, 시맨틱 태그로 이미 역할 명확)
- `CommunityDetailView.tsx` 158줄 — skill 가이드 100줄 초과 시 `ui/` 분리 권장이나, 상세 View 특성상 SearchForm/List 분리 불필요하므로 허용 범위

### 3. 테스트 — 80 / 100

브라우저 수동 검증 12개 시나리오 모두 통과. 자동화 테스트 없음 — 기존 프로젝트 방식과 동일하나 감점 기준 적용.

### 4. 보안 — 92 / 100

**양호:**
- `post.content` JSX 렌더링으로 XSS 방지 (innerHTML 미사용)
- `post.id`는 Mock 데이터 기반이라 사용자 입력 직접 사용 없음
- Open Redirect 방지: `isSafeRedirect` 로그인 페이지에서 처리
- 404 처리로 존재하지 않는 리소스 노출 방지
- 인증 조회 실패 전부 비로그인으로 흡수 (정책 명확)

**API 전환 시 주의:**
- `params.id`를 DB 쿼리에 직접 사용할 경우 파라미터 바인딩 필수 (현재는 Mock이므로 해당 없음)

### 5. 성능 — 95 / 100

- SSR로 초기 로딩 빠름
- Mock `Array.find()` O(30) — 무시할 수준
- 불필요한 상태 없음 (`comment` state만 사용)

### 6. 문서화 — 82 / 100

- Plan, Design 문서 존재 (Codex 리뷰 2회 반영)
- 코드 내 WHAT형 JSX 주석 다수 (감점)
- `catch {}` 블록 정책 주석은 적절 (WHY 명시)

---

## 종합 점수

| 영역 | 비중 | 점수 | 가중 점수 |
|------|------|------|-----------|
| 기능 완성도 | 20% | 98 | 19.6 |
| 코드 품질 | 20% | 87 | 17.4 |
| 테스트 | 20% | 80 | 16.0 |
| 보안 | 20% | 92 | 18.4 |
| 성능 | 10% | 95 | 9.5 |
| 문서화 | 10% | 82 | 8.2 |
| **합계** | | | **89.1** |

---

## 개선 제안 (Act 대상)

| 우선순위 | 영역 | 항목 |
|----------|------|------|
| 1 | 코드 품질 | JSX WHAT형 주석 4개 제거 |
| 2 | 문서화 | JSX 주석 제거로 자연스럽게 개선됨 |
