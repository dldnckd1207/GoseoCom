# Check Analysis — 번역 페이지 + 보호 Route

**Feature:** translate-page  
**Date:** 2026-04-22  
**Phase:** Check  

---

## 종합 점수: 72.2/100 (보통)

| 영역 | 점수 | 가중치 | 기여도 |
|------|------|--------|--------|
| 코드 품질 | 72/100 | 25% | 18.0 |
| 테스트 | 65/100 | 25% | 16.25 |
| 보안 | 78/100 | 20% | 15.6 |
| 성능 | 81/100 | 15% | 12.15 |
| 문서화 | 68/100 | 15% | 10.2 |

---

## 설계 vs 구현 의도적 변경 사항

> 아래 항목들은 구현 중 사용자 피드백으로 의도적으로 변경된 것이므로 결함이 아님

| 항목 | Design | 구현 | 이유 |
|------|--------|------|------|
| `_protected.tsx` 모달 | 없음 (silent redirect) | openModal('로그인이 필요합니다.') | UX 개선 — 사용자 요청 |
| `LoginView` sessionStorage | useEffect에서 저장 | onClick 핸들러에서 저장 | 방문만으로 저장 시 redirect 루프 버그 발견 → 수정 |

---

## 주요 이슈

### 🟡 코드 품질 (72)
- `'redirectAfterLogin'` 문자열이 3곳에 하드코딩 → 상수화 필요
- `isSafeRedirect` 검증 로직이 `_auth.tsx`와 `LoginView` 양쪽에 중복

### 🟡 테스트 (65)
- 수동 검증 적절 (순수 UI 상태 기반)
- typecheck/lint 통과

### ✅ 보안 (78)
- Open Redirect 방지 철저 (`startsWith('/') && !startsWith('//')`)
- `/login` 루프 방지
- sessionStorage try-catch 래핑

### ✅ 성능 (81)
- `/me` API 호출은 loader에서만 (중복 없음)

### 🟡 문서화 (68)
- 의도적 설계 변경에 대한 주석 부재

---

## 개선 우선순위

1. **`redirectAfterLogin` 상수화** — 3곳 하드코딩 → `shared/config/constants.ts`
2. **`isSafeRedirect` 유틸 추출** — `_auth.tsx`, `LoginView` 중복 제거
3. **`_protected.tsx` 설계 변경 주석** — 모달 추가 이유 명시
