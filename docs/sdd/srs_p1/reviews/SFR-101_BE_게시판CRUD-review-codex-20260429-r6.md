# SFR-101_BE_게시판CRUD 6차 재리뷰 - Codex

| 항목 | 내용 |
|------|------|
| 리뷰 대상 | `docs/sdd/srs_p1/SFR-101_BE_게시판CRUD.md` |
| 관련 확인 | `docs/specs/02_SRS.md`, `docs/specs/srs/SRS_P1.md`, `docs/specs/04_Domain.md` |
| 리뷰 일자 | 2026-04-29 |
| 리뷰어 | Codex |

## 총평

직전 리뷰에서 남긴 댓글 placeholder 관련 핵심 항목은 반영되었다.

- 댓글 목록 조회 흐름에 `del_yn=true` root placeholder 대상 포함 조건이 추가됨
- 댓글 응답 예시에 `is_deleted`가 추가됨
- 댓글 목록 `total`과 `post.comment_count`가 서로 다를 수 있음을 명시함
- `comment_count` 정의가 "삭제되지 않은 전체 댓글+대댓글 수"로 정리됨

현재 SFR-101은 구현 기준으로 충분히 닫아도 되는 수준이다. 남은 내용은 예시 JSON의 작은 정합성 문제다.

## 남은 발견 사항

### 1. [낮음] placeholder 예시가 placeholder 포함 조건과 맞지 않음

댓글 목록 정책은 "replies가 존재하는 `del_yn=true` root"만 placeholder 대상으로 포함한다고 되어 있다. 그런데 응답 예시의 삭제된 root 댓글 `CMT_00000003`은 `replies: []`이다.

이 상태면 아래 두 문장이 충돌한다.

- `total`: placeholder 포함 root 댓글 수 기준, replies 없는 `del_yn=true` root는 제외
- 예시: replies 없는 `del_yn=true` root가 items에 포함됨

권장 수정 중 하나를 선택하면 된다.

1. 예시에서 `CMT_00000003`에 대댓글 1개를 넣어 placeholder 포함 조건과 맞춘다.
2. 정책을 "삭제된 root는 replies 유무와 관계없이 placeholder로 포함"으로 단순화한다.

Phase 1 구현 단순성만 보면 2번이 더 쉽고, UX 관점에서 삭제된 단독 댓글까지 보여줄 필요가 없다면 1번이 더 깔끔하다.

### 2. [낮음] 댓글 목록 조회 흐름의 페이지네이션 기준을 한 문장 더 명확히 하면 좋음

현재도 충분히 이해 가능하지만, 구현자가 SQL을 작성할 때 헷갈리지 않도록 다음 정도의 문장을 추가하면 좋다.

- `total`과 page/size는 placeholder 포함 root 후보 집합 기준으로 계산한다.
- replies는 root 페이지네이션 이후 해당 root id 목록으로 별도 조회한다.

## 결론

남은 것은 예시와 조건의 작은 불일치뿐이다. 이 부분만 정리하면 더 이상 SFR-101 리뷰를 반복할 필요는 없어 보인다. 문서의 핵심 요구사항, 권한, 파일, 댓글 정책은 구현 가능한 수준으로 정리되어 있다.
