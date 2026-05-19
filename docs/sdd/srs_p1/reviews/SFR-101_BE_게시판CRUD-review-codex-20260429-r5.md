# SFR-101_BE_게시판CRUD 5차 재리뷰 - Codex

| 항목 | 내용 |
|------|------|
| 리뷰 대상 | `docs/sdd/srs_p1/SFR-101_BE_게시판CRUD.md` |
| 관련 확인 | `docs/specs/02_SRS.md`, `docs/specs/srs/SRS_P1.md`, `docs/specs/04_Domain.md`, `docs/specs/05_ERD.md`, `docs/sdd/srs_p1/SFR-105_BE_다중게시판.md` |
| 리뷰 일자 | 2026-04-29 |
| 리뷰어 | Codex |

## 총평

직전 4차 재리뷰에서 남긴 마무리 항목은 대부분 반영되었다.

- 댓글 응답 예시에 `is_deleted`가 추가됨
- 삭제 root 댓글 placeholder 예시가 추가됨
- `comment_count` 의미가 "삭제되지 않은 댓글+대댓글 수"로 명확해짐
- `file_ids` 중복 제거 정책이 요청 설명에 추가됨
- `attach_ext` 검증은 Phase 1에서 `file_ext` 기준, MIME 교차 검증은 Phase 2 이후로 명시됨

현재 문서는 Phase 1 구현 기준으로 충분히 안정적이다. 큰 구조적 누락이나 치명적인 문서 간 충돌은 보이지 않는다.

## 남은 발견 사항

### 1. [중간] 댓글 목록 조회 흐름과 placeholder 정책이 충돌함

댓글 목록 조회 흐름에는 `root 댓글 (parent_id=null, del_yn=false)`만 조회한다고 되어 있다. 그런데 아래 응답 정책에서는 soft delete된 root 댓글도 placeholder로 포함한다고 되어 있다.

권장 수정:
- 댓글 목록 조회 흐름 5단계를 다음처럼 바꾸면 된다.
  - `root 댓글 (parent_id=null, del_yn=false OR replies 존재하는 del_yn=true root placeholder 대상) → created_at ASC 페이지네이션`
- 또는 더 단순하게:
  - `root 댓글 조회 시 대댓글이 있는 del_yn=true root는 placeholder 대상으로 포함`

### 2. [낮음] 댓글 목록 응답 예시의 `total` 의미가 애매함

예시에는 items가 2개인데 `total`은 1이다. `total`이 삭제 placeholder를 제외한 root 수인지, 페이지에 실제 포함된 root row 수인지 불명확하다.

권장 수정:
- `total`을 페이지네이션 대상 root row 수로 둘지, 삭제되지 않은 root 댓글 수로 둘지 정의
- placeholder도 items에 들어간다면 보통 `total`도 placeholder 포함 root 기준이 구현이 단순하다
- 만약 placeholder 제외 카운트라면 `total` 설명에 "placeholder root 제외"를 명시

### 3. [낮음] `comment_count`와 `total`은 다른 값일 수 있음을 명시하면 좋음

`comment_count`는 삭제되지 않은 댓글+대댓글 수이고, 댓글 목록 `total`은 root 페이지네이션 기준이다. 둘은 의도적으로 다를 수 있다. 구현자와 프론트 혼동을 줄이려면 한 문장으로 분리해두면 좋다.

권장 문구:
- `post.comment_count`는 삭제되지 않은 전체 댓글+대댓글 수이다.
- 댓글 목록 `total`은 root 댓글 페이지네이션 기준이며, `comment_count`와 같지 않을 수 있다.

## 결론

이제 남은 내용은 댓글 목록의 placeholder 조회 조건과 `total` 정의를 다듬는 수준이다. 이 두 문장만 정리하면 SFR-101 문서는 구현 착수 기준으로 충분히 닫아도 된다.
