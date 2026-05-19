# SFR-101_BE_게시판CRUD 4차 재리뷰 - Codex

| 항목 | 내용 |
|------|------|
| 리뷰 대상 | `docs/sdd/srs_p1/SFR-101_BE_게시판CRUD.md` |
| 관련 확인 | `docs/specs/02_SRS.md`, `docs/specs/srs/SRS_P1.md`, `docs/specs/04_Domain.md`, `docs/specs/05_ERD.md`, `docs/sdd/srs_p1/SFR-105_BE_다중게시판.md` |
| 리뷰 일자 | 2026-04-29 |
| 리뷰어 | Codex |

## 총평

이전 리뷰에서 필수로 보았던 항목은 대부분 해소되었다.

- 게시글 수정 시 `file_ids` 검증이 작성 흐름과 동일하게 보강됨
- 파일 교체가 사전 검증 후 트랜잭션 안에서 처리되도록 명시됨
- root 댓글 삭제 정책이 placeholder 방식으로 확정됨
- `02_SRS.md`의 오래된 `POST /files` 문구가 최신 업로드 경로로 수정됨
- Domain의 `attach_size` 단위가 KB 기준으로 정리됨

현재 SFR-101은 Phase 1 구현 기준 문서로 사용해도 무리가 크지 않다. 남은 항목은 구현 전 마지막 정리 수준의 경미한 보완이다.

## 남은 발견 사항

### 1. [중간] root 댓글 placeholder 응답 필드가 예시 JSON에는 없음

본문에는 root 댓글이 soft delete된 경우 `content="삭제된 댓글입니다"`, `author_name=null`, `is_deleted=true`로 placeholder 반환한다고 명시되어 있다. 하지만 댓글 목록 응답 예시에는 `is_deleted` 필드가 없다.

권장 수정:
- 댓글 응답 예시에 `is_deleted: false`를 root/reply 모두 추가
- placeholder 예시를 짧게 하나 추가하거나, 필드 설명 표로 `is_deleted` 의미를 정의

### 2. [중간] root 댓글 삭제 후 `comment_count` 의미를 한 문장으로 고정하는 것이 좋음

현재 정책은 root 댓글 삭제 시 root만 `del_yn=true` 처리하고 대댓글은 유지하며 `comment_count -1`로 정리되어 있다. 이 경우 `comment_count`는 "삭제되지 않은 실제 댓글/대댓글 수"로 해석하면 일관된다. 다만 placeholder root는 목록에 노출되므로 화면에 보이는 행 수와 `comment_count`가 다를 수 있다.

권장 수정:
- `comment_count` 정의에 "placeholder로 노출되는 삭제 root 댓글은 카운트하지 않는다"를 추가

### 3. [낮음] 파일 중복 제거 정책은 에러 표에는 없어도 되지만 요청 설명에 한 줄 더 있으면 좋음

결정 사항에는 `dict.fromkeys(file_ids)`로 중복 제거한다고 정리되어 있다. 요청 스키마 설명에도 "중복 값은 서버에서 순서 보존 중복 제거 후 처리"를 추가하면 구현자와 프론트가 같은 기대를 갖기 쉽다.

### 4. [낮음] `attach_ext`와 MIME 검증의 우선순위가 구현 단계에서 필요함

Domain은 게시판 첨부가 `attach_ext` 설정을 따른다고 정리되었다. 실제 구현에서는 확장자만 볼지, MIME과 확장자를 모두 볼지 정해야 한다.

권장 수정:
- Phase 1은 최소 `file_ext` 기준으로 `attach_ext` 검증
- 가능하면 `mime_type`도 이미지/PDF 등 허용 타입과 교차 검증

## 결론

이제 큰 구조적 누락이나 문서 간 치명적 충돌은 보이지 않는다. 위 항목은 구현 전 polish에 가깝다. 특히 `is_deleted` 응답 예시와 `comment_count` 의미만 추가하면 SFR-101 문서는 충분히 안정적인 구현 기준으로 볼 수 있다.
