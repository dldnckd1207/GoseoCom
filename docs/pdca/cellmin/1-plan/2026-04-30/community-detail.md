# Plan: 커뮤니티 글 상세 페이지 (#99)

**작성일:** 2026-04-30
**작성자:** cellmin
**Redmine:** #99
**라우트:** `/community/:id`

---

## 1. 목표

커뮤니티 목록(`/community`)에서 게시글을 클릭했을 때 이동하는 글 상세 페이지 구현.
현재 스텁(`"준비 중입니다."`)을 실제 구현으로 교체한다.
API 연동 전까지 Mock 데이터 기반으로 구현하며, 추후 loader 교체만으로 API 전환 가능하도록 설계한다.

---

## 2. 요구사항

### 2-1. 기능 목록

| 기능 | 설명 |
|------|------|
| 게시글 상세 표시 | 시대 배지, 제목, 작성자, 날짜, 조회수, 본문 |
| 게시판별 접근 권한 | 게시판(탭)마다 회원/비회원 접근 여부 다름 |
| 비회원 접근 차단 | 권한 없으면 "회원 전용 게시판입니다." + 로그인 버튼 |
| 존재하지 않는 글 | HTTP 404 응답 + 한글 에러 페이지 (`root.tsx` ErrorBoundary) |
| 댓글 목록 | Mock 댓글 표시 |
| 댓글 작성 UI | 텍스트 입력 + 버튼 (실제 저장 없음, UI only) |
| 목록으로 돌아가기 | `/community` 링크 |

### 2-2. 게시판 권한 (Mock)

| 탭 | 레이블 | 비회원 접근 |
|----|--------|------------|
| translate | 번역 | ✅ 공개 |
| question | 질문 | ❌ 회원 전용 |
| free | 자유 | ✅ 공개 |

### 2-3. 비기능 요구사항

- SSR 기반 (`ssr: true`) — loader에서 권한 + 데이터 처리
- API 전환 시 View 변경 없이 loader만 교체 가능
- `_layout` 라우트 사용 (Header/Footer 포함)

---

## 3. 데이터 설계

### Post 타입 확장

```ts
export type Post = {
    id: string;
    title: string;
    tab: Exclude<PostTab, 'all'>;
    era: Exclude<PostEra, 'all'>;
    author: string;
    createdAt: string;
    content: string;     // 추가 — 게시글 본문
    viewCount: number;   // 추가 — 조회수
};
```

### Comment 타입 (신규)

```ts
export type Comment = {
    id: string;
    author: string;
    content: string;
    createdAt: string;
};
```

### BOARD_CONFIG (신규 — `views/community/config.ts`)

Mock 데이터와 권한 정책은 성격이 다르므로 별도 파일로 분리.

```ts
// apps/client/app/views/community/config.ts
export const BOARD_CONFIG: Record<
    Exclude<PostTab, 'all'>,
    { label: string; requiresLogin: boolean }
> = {
    translate: { label: '번역', requiresLogin: false },
    question:  { label: '질문', requiresLogin: true  },
    free:      { label: '자유', requiresLogin: false  },
};
```

---

## 4. 라우트 설계

### loader 흐름 (SSR)

```
1. params.id 존재 확인
   └─ 없으면 → throw redirect('/community')

2. MOCK_POSTS에서 params.id로 게시글 조회
   └─ 없으면 → throw new Response('Not Found', { status: 404 }) → ErrorBoundary 처리

3. serverFetch로 user 취득 (인증 조회 실패 시 user null 처리)

4. BOARD_CONFIG[post.tab].requiresLogin 확인
   └─ true && user === null → { post, boardConfig, accessDenied: true, comments: [], user: null }

5. 정상 → { post, boardConfig, accessDenied: false, comments, user }
```

### View 분기

```
accessDenied === true
  → "회원 전용 게시판입니다." + 로그인 버튼

accessDenied === false
  → 게시글 상세 + 댓글 섹션
```

---

## 5. 파일 구조

```
apps/client/app/
├── routes/
│   └── _layout.community.$id.tsx       # 스텁 → 실제 구현 (loader + default export)
├── views/community/
│   ├── CommunityDetailView.tsx          # 신규
│   ├── config.ts                        # 신규 — BOARD_CONFIG
│   ├── mock.ts                          # 수정 — content, viewCount 추가
│   └── mockComments.ts                  # 신규 — MOCK_COMMENTS, getComments
└── shared/types/
    └── post.ts                          # 수정 — content, viewCount 추가 / Comment 타입 신규
```

---

## 6. 성공 기준

- [ ] `/community/1` 진입 → 게시글 상세 정상 표시
- [ ] `/community/11` 진입 (question 탭) + 비로그인 → "회원 전용 게시판입니다." 화면 표시
- [ ] `/community/999` 진입 → HTTP 404 응답 + 한글 에러 페이지 (`root.tsx` ErrorBoundary)
- [ ] 댓글 목록 Mock 데이터 표시
- [ ] 댓글 작성 입력창 표시 (제출 시 `preventDefault` 처리, 입력값 초기화)
- [ ] 댓글 없을 때 "작성된 댓글이 없습니다." empty state 표시
- [ ] "목록으로" 링크 → `/community` 이동
- [ ] 로그인 버튼 → `<Link to="/login?redirect=/community/:id">` 이동 (LoginView가 query 값 처리)
- [ ] accessDenied 화면에도 "목록으로" 링크 표시
- [ ] TypeScript 에러 없음

---

## 7. 범위 외 (Out of Scope)

- 게시글 수정/삭제
- 댓글 실제 저장
- 좋아요/북마크
- 실제 조회수 증가 (Mock 고정값)
- API 연동 (추후 loader 교체로 대응)
