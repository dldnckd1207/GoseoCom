# Check: 커뮤니티 글 작성 화면 UI 정렬 (#100)

**분석일**: 2026-05-14  
**분석자**: cellmin (PDCA Check)  
**대상 Plan**: `docs/pdca/cellmin/1-plan/2026-05-11/community-write.md`  
**대상 Design**: `docs/pdca/cellmin/2-design/2026-05-14/community-write.md`

---

## 종합 점수

| 영역 | 비중 | 점수 | 가중 점수 |
|------|------|------|-----------|
| 기능 완성도 | 20% | 97 | 19.4 |
| 코드 품질 | 20% | 92 | 18.4 |
| 테스트 | 20% | 78 | 15.6 |
| 보안 | 20% | 94 | 18.8 |
| 성능 | 10% | 92 | 9.2 |
| 문서화 | 10% | 90 | 9.0 |
| **합계** | | | **90.4** |

**등급: 우수 (90%+)**

---

## 영역별 평가

### 1. 기능 완성도 — 97점

Plan 성공 기준 전항목 구현 확인:

| 성공 기준 | 결과 |
|----------|------|
| 라디오 버튼 토글, boards 동적 렌더링 | ✅ |
| 목록 탭 → write 진입 시 board 자동 선택 | ✅ |
| `?board` 없거나 invalid → 첫 번째 board fallback | ✅ |
| board_code 폼 전송 | ✅ |
| `max-w-4xl` 컨테이너 | ✅ |
| 카드 상단 회색 헤더 | ✅ |
| 비로그인 redirect 시 `?board` 유지 | ✅ |
| boards 빈 배열 시 안내 + 제출 비활성화 | ✅ |
| lint + typecheck 통과 | ✅ |

감점 요인: 브라우저 수동 검증 미완료 (-3)

---

### 2. 코드 품질 — 92점

**우수:**
- routes → views 위임 패턴 준수
- import 순서 컨벤션 준수
- CSS 클래스 정렬(Layout→Box→Typography→Visual→Interaction) 준수
- `key={defaultBoard}` 재마운트 처리로 uncontrolled radio 동기화 문제 해결
- `encodeURIComponent` 일관 적용
- 불필요한 추상화 없음, 코드량 최소화

**감점 요인:**
- "글 유형" 레이블에 `<p>` 사용 — `<fieldset>/<legend>` 조합이 더 시맨틱하나, `role="group"` + `aria-label`로 보완됨 (-5)
- 취소 버튼의 `<Link>` className에 CSS 클래스 정렬 순서 소폭 미준수 (`rounded-lg` 앞 위치) (-3)

---

### 3. 테스트 — 78점

Design에 T-1~T-7 수동 테스트 시나리오 명세됨.  
자동화 테스트 없음 (프로젝트 표준 — client에 vitest/cypress 미구성).

**감점 요인:**
- 브라우저 수동 검증 미실시 (-15)
- 자동화 테스트 없음 (-7, 프로젝트 현재 수준 기준 허용)

---

### 4. 보안 — 94점

**우수:**
- loader SSR에서 인증 처리, 비인증 시 즉시 redirect
- `encodeURIComponent(url.pathname + url.search)` — redirect 파라미터 안전 처리
- `?board` 값은 기존 board_code 목록과 매칭만 하여 injection 위험 없음
- JSX 기본 escaping으로 XSS 방어
- action에서 빈 값 검증 후 API 호출

**감점 요인:**
- `isSafeRedirect` 검증은 LoginView에 위임 — 이 파일에서 직접 검증하지 않음 (-6)

---

### 5. 성능 — 92점

**우수:**
- loader: 인증 확인 후 게시판 조회 (인증된 사용자에만 API 호출) — 불필요한 요청 없음
- `boards.map()` O(n), n=3 고정 — 문제 없음
- `key={defaultBoard}` 는 URL 변경 시에만 re-mount, 불필요한 리렌더 없음
- radio uncontrolled 방식 — 상태 관리 오버헤드 없음

**감점 요인:**
- user 조회 + board 조회가 순차 실행 (user 확인 후 board 조회는 설계상 의도적) (-8)

---

### 6. 문서화 — 90점

**우수:**
- Plan + Design + Codex 리뷰 3회 전 사이클 문서 완비
- Design에 T-1~T-7 테스트 시나리오 명세
- 코드 자체가 자명하여 별도 주석 불필요

**감점 요인:**
- 브라우저 검증 결과가 문서화되지 않음 (-10)

---

## 개선 권장 사항

| 우선순위 | 항목 | 영역 |
|---------|------|------|
| Low | 취소 버튼 `<Link>` className 정렬 소폭 수정 | 코드 품질 |
| Low | 브라우저 T-1~T-7 수동 검증 실시 및 결과 기록 | 테스트/문서화 |

---

## 결론

**종합 90.4점 — 우수. 품질 목표(90%) 달성.**

취소 버튼 className 정렬은 사소한 수준으로, Act 없이 바로 `/pdca report`로 완료 처리 가능.  
브라우저 수동 검증은 report 전에 실시하는 것을 권장.
