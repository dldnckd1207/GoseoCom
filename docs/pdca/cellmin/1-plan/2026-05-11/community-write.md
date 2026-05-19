# Plan: 커뮤니티 글 작성 화면 UI 정렬 (#100)

**작성자**: cellmin  
**날짜**: 2026-05-11 (업데이트: 2026-05-14)  
**관련 이슈**: Redmine #100

---

## 1. 배경 및 목표

커뮤니티 글 작성 페이지(`/community/write`)의 loader / action / API 연결은 #104에서 완료됨.  
목업(`docs/designs/client/write-post.html`) 대비 UI 차이가 남아 있어 이를 정렬하는 것이 이번 작업의 목표.

**"시대" 필드는 이번 범위에서 제외** — BoardCategory API(#108) 완료 후 별도 반영.

---

## 2. 요구사항

### 기능 요구사항

| # | 항목 | 설명 |
|---|------|------|
| F-1 | 글 유형 라디오 버튼 그룹 | `<select>` → `<input type="radio">` 기반 버튼 토글 그룹. loader의 `boards` 배열을 동적으로 렌더링 (하드코딩 금지) |
| F-2 | 초기 선택값 | `?board=board_code` 쿼리 파라미터와 일치하는 board 자동 선택. 쿼리 없거나 유효하지 않은 board_code면 첫 번째 board 선택 |
| F-3 | 목록 → 작성 연동 | 목록 페이지 글 작성 버튼 클릭 시 현재 탭을 `?board=` 로 전달. `tab=all`이면 파라미터 없이 이동 |
| F-6 | 비로그인 redirect `?board` 유지 | loader에서 비로그인 redirect 시 `/login?redirect=` 값을 하드코딩 대신 request URL(pathname + search) 기반으로 구성 → 로그인 후 `?board` 파라미터가 유지된 채 복귀 |
| F-7 | boards 빈 배열 fallback | boards가 비어 있으면 글 유형 영역에 "게시판 정보를 불러오지 못했습니다" 안내 표시 + 제출 버튼 비활성화 |
| F-4 | 컨테이너 너비 확장 | `max-w-3xl` → `max-w-4xl` |
| F-5 | 폼 헤더 스타일 | 카드 상단에 회색 배경 헤더 영역 분리 (`글 작성하기` 타이틀) |

### 비기능 요구사항

| # | 항목 |
|---|------|
| N-1 | `npm run lint` + `npm run typecheck` 오류 없음 |
| N-2 | action의 submit contract 변경 없음. loader의 boards 조회 contract는 유지하되 `defaultBoard`만 추가 반환 |
| N-3 | 반응형 유지 (sm 브레이크포인트) |
| N-4 | 글 유형 영역은 전체 폭 배치 (시대 필드 없으므로 반쪽 레이아웃 금지) |

### 제외 범위

- "시대" 선택 필드 — #108 (BoardCategory API) 완료 후 반영
- action / API 로직 변경
- loader의 게시판 조회 로직 변경 (단, `?board` 쿼리 파싱 및 `defaultBoard` 반환은 이번 범위에 포함)

---

## 3. 기술 스택

- React Router v7 (framework mode)
- TypeScript
- Tailwind CSS v4
- CSS 변수 (`--text-*` 폰트 크기 토큰)

---

## 4. 변경 파일

| 파일 | 변경 유형 | 설명 |
|------|-----------|------|
| `apps/client/app/views/community/CommunityWriteView.tsx` | 수정 | 라디오 버튼 그룹, 레이아웃, 헤더 스타일 |
| `apps/client/app/routes/_layout.community.write.tsx` | 수정 | loader에서 `?board` 쿼리 읽어 `defaultBoard` 반환 |
| `apps/client/app/views/community/CommunityListView.tsx` | 수정 | 글 작성 버튼 navigate에 `?board=${currentTab}` 추가 |

---

## 5. 성공 기준

- [ ] 글 유형이 라디오 버튼 토글로 표시되며 하나만 선택 가능
- [ ] 목록에서 "번역" 탭 선택 후 글 작성 클릭 → 번역 자동 선택
- [ ] 목록에서 "전체" 탭이거나 직접 URL 입력 시 → 첫 번째 board 선택
- [ ] 유효하지 않은 `?board=` 값이면 첫 번째 board로 fallback
- [ ] 선택된 board_code가 폼 제출 시 정상 전송됨
- [ ] 컨테이너가 `max-w-4xl`로 확장됨
- [ ] 카드 상단에 회색 헤더 영역(`글 작성하기`)이 목업과 유사하게 표시됨
- [ ] `npm run lint` + `npm run typecheck` 통과
- [ ] 비로그인 상태로 `/community/write?board=translation` 접근 → 로그인 후 해당 URL로 복귀되어 번역 자동 선택
- [ ] boards가 빈 배열일 때 안내 메시지 표시 + 제출 버튼 비활성화
- [ ] 브라우저에서 글 작성 → 제출 → 상세 페이지 이동 정상 동작
