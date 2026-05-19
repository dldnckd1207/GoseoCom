# Plan — 커뮤니티 목록 페이지 (#98)

- **작성자:** cellmin
- **날짜:** 2026-04-28
- **Redmine:** #98
- **부모 이슈:** #95

---

## 1. 목표 & 범위

`/community` 경로에 커뮤니티 게시글 목록 페이지를 구현한다.
- 공개 라우트 (`_layout` 사용, 로그인 불필요)
- Mock 데이터 사용 → 백엔드 완성 후 loader에서 API 호출로 교체
- API 전환 시 `_layout.community._index.tsx`에 child loader를 추가하고 필터/페이지네이션 쿼리를 서버 파라미터로 전달한다

**범위 포함:**
- 탭 필터 (게시글 유형)
- 시대 드롭다운 필터
- 게시글 테이블
- 페이지네이션 (Mock 30개, 3페이지 표시)
- 글 작성하기 버튼
- `/community/:id` 라우트 스텁 (#99 구현 전까지 빈 화면)
- `/community/write` 라우트 스텁 (#100 구현 전까지 빈 화면)

**범위 제외:**
- 실제 API 연동 (Mock 데이터)
- 검색 기능
- 글 상세 구현 (#99), 글 작성 구현 (#100)

---

## 2. 요구사항

### 탭 필터
| slug | 레이블 |
|------|--------|
| `all` | 전체 |
| `translate` | 번역 |
| `question` | 질문 |
| `free` | 자유 |

### 시대 드롭다운
| slug | 레이블 |
|------|--------|
| `all` | 전체 |
| `prehistoric` | 선사 |
| `samguk` | 삼국 |
| `goryeo` | 고려 |
| `joseon` | 조선 |

### 게시글 테이블 컬럼
- 제목 (클릭 시 상세 페이지 이동)
- 카테고리(시대)
- 작성자
- 작성일

### 글 작성하기 버튼
- 모든 사용자에게 표시
- 비로그인 클릭 시 로그인 안내 모달 표시
- 로그인 사용자 클릭 시 `/community/write` 이동

### 필터 & 페이지네이션 상태 관리
- URL 쿼리스트링으로 관리: `?tab=translate&era=joseon&page=2`
- 새로고침/뒤로가기/링크 공유 시 상태 유지
- `useSearchParams()` 사용

---

## 3. 파일 구조

```
routes/
  _layout.community._index.tsx   # /community 목록 라우트
  _layout.community.$id.tsx      # /community/:id 스텁
  _layout.community.write.tsx    # /community/write 스텁
views/
  community/
    CommunityListView.tsx         # 페이지 뷰
    mock.ts                       # Mock 게시글 데이터 (30개)
shared/types/
  post.ts                         # Post 타입 정의
```

---

## 4. 성공 기준

- [ ] `/community` 접근 시 목록 페이지 렌더링
- [ ] 탭 클릭 시 URL `?tab=` 업데이트, 필터 적용
- [ ] 시대 드롭다운 변경 시 URL `?era=` 업데이트, 필터 적용
- [ ] 페이지 번호 클릭 시 URL `?page=` 업데이트
- [ ] 새로고침해도 탭/시대/페이지 상태 유지
- [ ] 비로그인 상태에서 글 작성하기 클릭 시 로그인 안내 모달 → 확인 시 `/login?redirect=/community/write` 이동
- [ ] 로그인 상태에서 글 작성하기 클릭 시 `/community/write` navigate
- [ ] 게시글 행 클릭 시 `/community/:id` navigate (스텁 라우트로 이동)
- [ ] 페이지네이션 버튼 3개 표시 (Mock 30개 기준)
- [ ] 목업 디자인(`community.html`) 기준 UI 일치 (페이지 수는 데이터 기준 동적)
- [ ] TypeScript 타입 오류 없음
