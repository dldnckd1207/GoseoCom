# Check: 게시판 카테고리 API 구현 (sfr-108-board-category)

**분석일**: 2026-05-16 (마이그레이션·브라우저 검증 전)  
**분석자**: cellmin (PDCA Check)

---

## 종합 점수

| 영역 | 비중 | 점수 | 가중 점수 |
|------|------|------|-----------|
| 기능 완성도 | 20% | 95 | 19.0 |
| 코드 품질 | 20% | 93 | 18.6 |
| 테스트 | 20% | 70 | 14.0 |
| 보안 | 20% | 92 | 18.4 |
| 성능 | 10% | 90 | 9.0 |
| 문서화 | 10% | 88 | 8.8 |
| **합계** | | | **87.8** |

**등급: 양호 — 마이그레이션 + 브라우저 검증 후 90+ 예상**

---

## 영역별 평가

### 1. 기능 완성도 — 95점

| 항목 | 결과 |
|------|------|
| 마이그레이션 2개 (chain 올바름) | ✅ |
| `GET /api/v1/boards/{board_code}/categories` API | ✅ |
| `PostCreateRequest.category_id` 추가 | ✅ |
| category 소속 검증 (INVALID_CATEGORY / CATEGORY_NOT_ALLOWED) | ✅ |
| FE loader 병렬 카테고리 조회 | ✅ |
| FE action `category_id` POST body 포함 | ✅ |
| "시대" 드롭다운 UI (선택 안 함 포함) | ✅ |
| `<select key={selectedBoard}>` board 변경 시 초기화 | ✅ |
| BE ruff + mypy 통과 | ✅ |
| FE lint + typecheck 통과 | ✅ |

감점: 브라우저 검증 미완료 (-5)

---

### 2. 코드 품질 — 93점

**우수:**
- Router → Service → Repository 레이어 분리 준수
- `BoardCategoryResponse` 별도 스키마로 분리
- `Promise.allSettled`로 카테고리 조회 실패 격리
- `selectedBoard` useState + `<select key>` 조합으로 초기화 처리
- CSS 클래스 정렬 컨벤션 준수

**감점:**
- `CommunityWriteView`의 카테고리 섹션이 글 유형 섹션과 비슷한 패턴이나, 별도 컴포넌트로 분리되지 않음 (-7, 현 범위에서 허용)

---

### 3. 테스트 — 70점

- 자동화 테스트 없음 (프로젝트 표준)
- T-1~T-9 시나리오 Design에 명세 완료
- 브라우저 검증 미실시

감점: -30 (브라우저 미검증)

---

### 4. 보안 — 92점

**우수:**
- `category_id` 존재 여부 + board 소속 검증
- `Board.category_yn=false`인 경우 400 반환
- `GET /categories` 공개 API이지만 category 삽입/수정은 인증 필요한 post API 경유
- XSS: JSX 기본 escaping

**감점:**
- `GET /categories`에 rate limiting 없음 (-8, 현 단계에서 허용)

---

### 5. 성능 — 90점

**우수:**
- `Promise.allSettled` 병렬 카테고리 조회 — 직렬 N+1 없음
- 카테고리 조회 실패 시 빠른 fallback (빈 배열)
- `Board` JOIN `BoardCategory` 단일 쿼리

감점: 카테고리 결과 캐싱 없음 (-10, Phase 2 이슈)

---

### 6. 문서화 — 88점

- Plan + Design + Codex 리뷰 2회 전 사이클 완비 ✅
- T-1~T-9 테스트 시나리오 명세 ✅
- 브라우저 검증 결과 미기록 (-12)

---

## 브라우저 검증 시나리오

| # | 시나리오 | 기대 |
|---|----------|------|
| T-1 | `GET /api/v1/boards/translation/categories` | 선사/삼국/고려/조선 4개 반환 |
| T-2 | 글 작성 페이지 진입 | 글 유형 아래 "시대" 드롭다운 표시 |
| T-3 | 글 유형 변경 | 해당 게시판 카테고리로 드롭다운 갱신 |
| T-4 | 시대 선택 후 글 작성 | DB에 category_id 저장 |
| T-5 | 시대 미선택 후 글 작성 | category_id=null로 정상 저장 |
| T-6 | 다른 게시판 category_id로 글 작성 (curl) | 400 INVALID_CATEGORY |
| T-7 | 존재하지 않는 category_id로 글 작성 (curl) | 400 INVALID_CATEGORY |
| T-8 | 카테고리 미선택 action payload 확인 | category_id=null |
| T-9 | 카테고리 API 일부 실패 시 | 해당 board만 빈 배열, 화면 유지 |
