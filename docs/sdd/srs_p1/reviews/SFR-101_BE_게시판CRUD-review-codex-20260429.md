# SFR-101_BE_게시판CRUD 재리뷰 - Codex

| 항목 | 내용 |
|------|------|
| 리뷰 대상 | `docs/sdd/srs_p1/SFR-101_BE_게시판CRUD.md` |
| 관련 수정 확인 | `docs/specs/srs/SRS_P1.md` 일부 수정 확인 |
| 기준 문서 | `docs/specs/01_PRD.md`, `docs/specs/02_SRS.md`, `docs/specs/srs/SRS_P1.md`, `docs/specs/04_Domain.md`, `docs/specs/05_ERD.md`, `docs/sdd/srs_p1/SFR-105_BE_다중게시판.md` |
| 리뷰 일자 | 2026-04-29 |
| 리뷰어 | Codex |

## 총평

이전 리뷰의 핵심 지적 대부분은 반영되었다. 특히 파일 첨부, `read_yn`/`guest_read_yn` 분기, 공지 기능 플래그, 댓글 소속 검증, 답글/대댓글 depth 검증, ADMIN 권한 정책이 문서에 추가되어 구현 기준으로 훨씬 명확해졌다.

다만 아직 **결정 사항 표에 "파일 첨부 Phase 1 제외" 문구가 남아 있어 본문과 직접 충돌**한다. 또한 `file_ids`를 설명에 추가했지만 요청 스키마 예시에는 빠져 있고, 업로드 API 경로가 `SFR-101`과 `SRS_P1` 사이에서 `{board_code}`/`{board_id}`로 갈라져 있다. 이 세 가지는 구현자가 바로 혼동할 수 있어 수정 우선순위가 높다.

## 반영 확인

- 파일 첨부가 Phase 1 범위로 본문에 복구됨
- 게시글 단건 응답에 `files[]` 포함
- 읽기 권한이 비회원 `guest_read_yn`, 로그인 `read_yn`으로 분리됨
- 공지 작성/수정 시 `board.notice_yn` 검증 추가
- 댓글 수정/삭제 시 `(comment_id, post_id)` 조건 조회 명시
- 답글/대댓글 parent 존재, 소속, depth 검증 추가
- ADMIN/SYSTEM_ADMIN을 Phase 1 권한 레벨로 활성화하도록 `SRS_P1` 수정
- AI 시드 계정 ID를 `USR_00000000`으로 SFR-101 결정 사항에 명시

## 남은 발견 사항

### 1. [높음] 파일 첨부 결정 사항이 본문과 충돌함

- 대상: `SFR-101_BE_게시판CRUD.md` 결정 사항 표의 `파일 첨부` 행
- 현재 내용: `Phase 1 제외`, `core/files 모듈 미구현 — SFR-102 별도`
- 충돌 내용:
  - 배경/기능/흐름/미결 항목에서는 파일 첨부를 Phase 1 포함으로 정리함
  - `SFR-102`는 상위 SRS에서 OCR 기능이었고 현재 SFR-106에 흡수된 항목이라 파일 첨부 근거로 부적절함

권장 수정:
- `파일 첨부 | Phase 1 포함: 선업로드 + file_map 연결 | PRD/SRS Must 범위이며 게시판/번역기 공통 파일 인프라 재사용 | CRUD와 분리 구현하되 SFR-101에서 매핑 처리`
  정도로 바꾸는 것이 일관된다.

### 2. [높음] `file_ids`가 요청 스키마 예시에 빠져 있음

- 대상: `POST /api/v1/posts` 요청, `PUT /api/v1/posts/{post_id}` 요청
- 현재 본문 흐름은 `file_ids` 수신과 `file_map INSERT`를 명시하지만, JSON 예시는 여전히 파일 없는 형태다.

권장 수정:
```json
{
  "board_code": "translation",
  "title": "제목",
  "content": "본문 내용",
  "notice_yn": false,
  "parent_id": null,
  "file_ids": ["FILE_00000001"]
}
```

수정 요청은 "최종 첨부 목록 교체"인지, "add_file_ids/remove_file_ids" 방식인지도 결정해야 한다. 현재 "변경 필드만" PUT과 `file_ids 선택` 설명만으로는 파일 탈부착 동작이 모호하다.

### 3. [높음] 게시판 업로드 API 경로가 문서 간 불일치함

- `SFR-101`: `POST /api/v1/boards/{board_code}/uploads`
- `SRS_P1`: `POST /api/v1/boards/{board_id}/uploads`
- `SFR-105`: 클라이언트 단건 조회는 `{board_code}`, 관리자 단건 조회는 `{board_id}` 패턴

권장 수정:
- 클라이언트 게시판 컨텍스트 업로드라면 `{board_code}`가 더 자연스럽다.
- `SRS_P1 §3.4`도 `POST /api/v1/boards/{board_code}/uploads`로 맞추거나, 둘 다 허용하지 않을 거라면 하나로 통일해야 한다.

### 4. [중간] 첨부 정책에서 `attach_yn=false` + `file_ids` 전달 시 처리가 빠져 있음

- 현재 흐름: `attach_yn=true이고 file_ids 전달 시 게시판 첨부 정책 검증`
- 문제: `attach_yn=false`인데 `file_ids`가 전달된 경우의 에러가 명시되지 않음

권장 수정:
- `file_ids`가 비어 있지 않고 `attach_yn=false`이면 403 또는 400 계열 에러를 반환하도록 정의
- 에러 코드 예: `ATTACH_NOT_ALLOWED`
- `attach_count`, `attach_size`, `attach_ext` 초과/불일치 에러 코드도 표에 추가

### 5. [중간] 파일 접근/업로드 경로가 Domain 문서와도 불일치함

- `SRS_P1`: `POST /api/v1/uploads`, `GET /files/{uuid}`
- `Domain`: `POST /files`, `GET /files/:id`
- `SFR-101`: `POST /api/v1/boards/{board_code}/uploads`, 응답 `url_path: /files/uuid-here`

상위 Domain 문서가 오래된 표현일 가능성이 높다. 구현 기준을 SRS_P1/SFR-101로 둘 거라면 Domain의 FBR-01/FBR-06도 최신 경로로 갱신하는 편이 좋다.

### 6. [중간] PostHistory Phase 정책이 Domain 문서와 아직 충돌함

- `SFR-101`: Phase 1부터 수정/삭제 시 `cms_th_post_history` INSERT
- `Domain`: PostHistory는 Phase 1 스키마 선반영, INSERT는 Phase 3에서 시작

SFR-101의 방향이 더 구현 친화적이므로, Domain의 PostHistory 설명을 갱신하는 것을 권장한다.

### 7. [중간] AI 시드 계정 ID가 Domain 문서에는 아직 `USER_00000000`으로 남아 있음

- `SFR-101`, `SRS_P1`, `ERD`: `USR_00000000`
- `Domain`: `USER_00000000`

SFR-101에서 "USER_00000000 아님"이라고 명시한 것은 좋지만, 기준 문서인 Domain에 남아 있으면 계속 혼선이 난다. Domain도 `USR_00000000`으로 통일하는 것이 맞다.

### 8. [낮음] 댓글 작성 권한에서 `read_yn` 또는 게시판 활성 상태 검증의 재사용 여부가 애매함

댓글 작성은 `post`를 통해 board를 조회한 뒤 `comment_yn`만 확인한다. 이미 `post`가 존재하려면 board가 정상이라고 볼 수도 있지만, 게시판이 이후 `use_yn=false`로 바뀐 경우 댓글 작성을 막을지 정책이 필요하다.

권장 수정:
- 작성 계열에서는 board `use_yn=true`, `del_yn=false`를 전제로 다시 확인한다고 명시
- 필요하면 `write_yn=false`가 댓글 작성까지 막는지, 댓글은 `comment_yn`만 따르는지도 결정

### 9. [낮음] 에러 응답 표가 새 정책을 따라가지 못함

추가된 정책에 비해 에러 표에는 다음이 없다.

- `read_yn=false` 로그인 사용자 접근
- `attach_yn=false`
- 첨부 확장자/크기/개수 위반
- parent post/comment 없음 또는 depth 초과
- `board.notice_yn=false`

기존 코드인 `FORBIDDEN`, `REPLY_NOT_ALLOWED`로 재사용할 수도 있지만, 표에서 매핑을 명확히 해두는 것이 구현/테스트에 좋다.

## 결론

SFR-101 문서 자체는 이전보다 구현 가능한 상태에 가까워졌다. 남은 핵심 수정은 다음 순서로 처리하면 된다.

1. 결정 사항 표의 `파일 첨부 Phase 1 제외` 잔존 문구 제거
2. `file_ids` 요청 스키마와 파일 수정 정책 보강
3. 업로드 API 경로를 `{board_code}` 또는 `{board_id}` 중 하나로 통일
4. Domain의 `USER_00000000`, `POST /files`, PostHistory Phase 문구를 SRS_P1/SFR-101 기준으로 갱신
