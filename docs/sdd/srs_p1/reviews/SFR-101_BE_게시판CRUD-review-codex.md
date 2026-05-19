# SFR-101_BE_게시판CRUD 리뷰 - Codex

| 항목 | 내용 |
|------|------|
| 리뷰 대상 | `docs/sdd/srs_p1/SFR-101_BE_게시판CRUD.md` |
| 기준 문서 | `docs/specs/01_PRD.md`, `docs/specs/02_SRS.md`, `docs/specs/srs/SRS_P1.md`, `docs/specs/04_Domain.md`, `docs/specs/05_ERD.md`, `docs/sdd/srs_p1/SFR-105_BE_다중게시판.md` |
| 리뷰 일자 | 2026-04-28 |
| 리뷰어 | Codex |

## 총평

SFR-101 문서는 게시글/댓글 CRUD의 기본 흐름, 권한, 카운터, 댓글 중첩 정책을 구현 가능한 수준으로 잘 정리하고 있다. 특히 `view_count`/`comment_count` 원자적 갱신, `author_name` 스냅샷, 댓글 depth=1 제한은 구현 판단이 명확하다.

다만 현재 문서는 상위 SRS/PRD와 비교했을 때 **파일 첨부 범위가 가장 크게 누락**되어 있다. 또한 `read_yn` 권한, 공지 기능 플래그, PostHistory Phase 정책, 응답 스키마의 첨부파일/수정삭제 응답, API 경로 참조 일부가 서로 맞지 않는다. 아래 항목을 보정한 뒤 구현에 들어가는 것을 권장한다.

## 주요 발견 사항

### 1. [높음] SFR-101의 Phase 1 파일 첨부 범위가 누락됨

- 대상 문서: `SFR-101_BE_게시판CRUD.md` 29행, 292-300행, 349-373행, 443행
- 기준 문서:
  - `02_SRS.md` 115행: SFR-101은 "파일 업로드 분리 + file_map 매핑 포함"
  - `02_SRS.md` 174-181행: 게시글 작성은 첨부 파일 ID 리스트를 받고, 상세 조회는 `file_map` 조인으로 첨부파일 포함
  - `SRS_P1.md` 106-156행: 게시판 파일 업로드/서빙, `file_map` 첨부/탈부착 패턴이 Phase 1 공통 규칙
  - `01_PRD.md`: Phase 1 로드맵에 파일 업로드 포함

현재 SFR-101은 "Phase 1에서는 파일 첨부 제외"라고 명시하고, 요청/응답 스키마에도 `file_ids`, `files`가 없다. 이는 상위 SRS의 Must 범위를 축소하는 내용이다. 실제 구현자가 이 문서를 따르면 게시판 CRUD는 파일 없는 CRUD가 되어 PRD/SRS와 불일치한다.

권장 보정:
- 게시글 작성 요청에 `file_ids: string[]` 추가
- 게시글 상세 응답에 첨부 파일 목록 추가
- 게시글 수정 시 파일 매핑 추가/해제 정책 명시
- 게시판 설정 `attach_yn`, `attach_ext`, `attach_size`, `attach_count` 검증 흐름 추가
- 업로드 API는 `SRS_P1` 기준인 `POST /api/v1/boards/{board_id}/uploads` 또는 문서 전체에서 확정한 최신 경로로 통일

### 2. [높음] 읽기 권한에서 `read_yn` 체크가 빠져 있음

- 대상 문서: `SFR-101_BE_게시판CRUD.md` 26행, 56-62행, 68-74행, 127-129행
- 기준 문서:
  - `SFR-105_BE_다중게시판.md` 144-145행: `read_yn`, `guest_read_yn` 모두 존재
  - `05_ERD.md` 341-342행: 로그인 사용자 읽기 허용과 비회원 읽기 허용이 분리됨

현재 SFR-101은 비회원의 `guest_read_yn=false`만 차단한다. 로그인 사용자의 읽기 권한은 `read_yn`을 봐야 하는데 목록/단건/댓글 목록 흐름에 없다.

권장 보정:
- Optional 인증 결과가 로그인 사용자이면 `read_yn=true` 확인
- 비회원이면 `guest_read_yn=true` 확인
- 에러 코드는 `BOARD_READ_FORBIDDEN`으로 통일하거나, 로그인/비회원 구분 코드를 별도 정의

### 3. [높음] ADMIN 권한 사용 방식이 Phase 1 권한 정책과 충돌 가능

- 대상 문서: `SFR-101_BE_게시판CRUD.md` 28행, 40행, 85행, 99-103행
- 기준 문서:
  - `SRS_P1.md` 64-69행: ADMIN/SYSTEM_ADMIN은 Phase 1 비활성
  - `SFR-105_BE_다중게시판.md`는 ADMIN API를 Phase 1에 구현한다고 되어 있어 문서 간 정책 자체도 일부 충돌

SFR-101은 본인 또는 ADMIN 이상, 공지 설정 ADMIN 이상을 구현 전제로 둔다. 그런데 SRS_P1 공통 권한 표에서는 ADMIN이 Phase 3 비활성이다. 구현 관점에서 `require_level(ADMIN)` 또는 관리자 bypass를 넣어야 하는지, Phase 1에서는 사실상 본인만 허용해야 하는지 불명확하다.

권장 보정:
- Phase 1에서 ADMIN API/권한을 실제 활성화할지 공통 정책을 먼저 확정
- 비활성이라면 "Phase 1 런타임에서는 본인만 가능, ADMIN override는 권한 활성화 후 동작"처럼 명시
- 활성화라면 `SRS_P1 §3.2`의 ADMIN 비활성 표를 수정

### 4. [중간] 공지 작성 시 `board.notice_yn` 검증이 작성 흐름에서 빠짐

- 대상 문서: `SFR-101_BE_게시판CRUD.md` 83-86행, 101-103행
- 기준 문서:
  - `SFR-105_BE_다중게시판.md` 148행: `notice_yn`은 공지 기능 허용 여부

수정 흐름에는 `board.notice_yn=false`일 때 공지 설정 불가가 있으나, 작성 흐름에는 USER 권한 차단만 있고 게시판 공지 기능 플래그 검증이 없다. ADMIN이 공지글을 작성하는 경우 `notice_yn=false` 게시판에서도 작성 가능하게 해석될 수 있다.

권장 보정:
- 작성 흐름에도 `notice_yn=true` 요청 시 `board.notice_yn=true` 확인 단계를 추가

### 5. [중간] PostHistory 정책이 Domain 문서와 다름

- 대상 문서: `SFR-101_BE_게시판CRUD.md` 39행, 104행, 117행, 228-239행, 441행
- 기준 문서:
  - `04_Domain.md` 387-400행: PostHistory는 Phase 1 스키마 선반영, INSERT는 Phase 3 관리자 페이지에서 시작
  - `05_ERD.md` 458-465행: Phase 1 선반영

SFR-101은 수정/삭제 시 PostHistory INSERT를 Phase 1 구현으로 요구한다. 이 방향 자체는 게시글 복구와 감사 추적에 유리하지만, Domain 문서의 "INSERT는 Phase 3에서 시작"과 충돌한다.

권장 보정:
- SFR-101 기준으로 Phase 1부터 UPDATE/DELETE 이력을 남길지 확정
- Phase 1 구현이면 Domain의 PostHistory 설명을 갱신
- Phase 3부터라면 SFR-101의 수정/삭제 흐름에서 history INSERT를 "Phase 3 확장"으로 내려야 함

### 6. [중간] AI 시드 계정 ID 표기가 상위 문서와 일부 불일치

- 대상 문서: `SFR-101_BE_게시판CRUD.md` 442행
- 기준 문서:
  - `SRS_P1.md` 101행, 160-162행: `USR_00000000`
  - `04_Domain.md` 68행, 81행, 439행: 일부는 `USER_00000000`으로 표기
  - `05_ERD.md` 105행: `USR_00000000`

SFR-101은 `USR_00000000`을 사용해 SRS_P1/ERD와 맞지만, Domain/Architecture 일부에는 `USER_00000000` 표기가 남아 있다. 구현 시 seed ID, 테스트 픽스처, `is_ai_gen` 판별이 달라질 수 있다.

권장 보정:
- 최종 표기는 `USR_00000000`으로 통일하는 것이 SRS_P1/ERD의 ID-Gen 규칙과 맞음
- SFR-101 참고 문서에도 "AI 계정 ID는 `USR_00000000` 기준"을 명시

### 7. [중간] 댓글 작성/수정/삭제에서 post-comment 소속 검증이 명시되지 않음

- 대상 문서: `SFR-101_BE_게시판CRUD.md` 140-162행, 275-278행

댓글 수정/삭제 API는 `/posts/{post_id}/comments/{comment_id}` 형태인데, 흐름은 `comment_id` 존재와 권한만 확인한다. `comment.post_id == path.post_id` 검증이 없으면 잘못된 URL 조합에서도 다른 게시글 댓글이 수정/삭제될 수 있다.

권장 보정:
- 댓글 조회/수정/삭제는 `comment_id` 단독 조회 후 `post_id` 일치 검증 또는 `(comment_id, post_id)` 조건 조회로 명시
- 불일치 시 404 `COMMENT_NOT_FOUND` 권장

### 8. [중간] 답글/대댓글 depth 제한 검증이 상세 흐름에 부족함

- 대상 문서: `SFR-101_BE_게시판CRUD.md` 41행, 140-150행, 446-447행

게시글 답글과 댓글 대댓글 모두 depth=1 제한을 의사결정으로 두었지만, 실제 작성 흐름에는 parent의 존재 여부, parent가 같은 board/post에 속하는지, parent.depth=0인지 검증이 빠져 있다.

권장 보정:
- 게시글 답글 작성: `parent_id` 존재, 같은 `board_id`, `parent.depth=0`, `reply_yn=true` 확인
- 댓글 대댓글 작성: `parent_id` 존재, 같은 `post_id`, `parent.depth=0` 확인
- depth=1을 초과하는 요청은 400 또는 403 계열 에러로 정의

### 9. [중간] 응답 스키마가 구현에 필요한 필드를 일부 누락함

- 대상 문서: `SFR-101_BE_게시판CRUD.md` 321-373행, 376-412행

상세 응답에 `files`, `secret_yn`, `like_count`, `auto_reply_at`, `updated_at` 외 삭제 관련 표시 정책 등이 명시되지 않았다. Phase 1에서 좋아요/비밀글이 미노출이라면 괜찮지만, 파일은 상위 요구사항상 포함되어야 한다. 댓글 응답도 `updated_at`, `parent_id`, `like_count`, `is_filtered` 포함 여부가 불명확하다.

권장 보정:
- Phase 1 API에서 노출할 필드를 표로 확정
- 게시글 상세에는 최소 `files[]` 포함
- 댓글 응답에는 `parent_id`, `updated_at` 포함 여부를 명시

### 10. [낮음] SFR-101 참고 링크 경로가 실제 파일명과 다름

- 대상 문서: `SFR-101_BE_게시판CRUD.md` 참고 섹션

현재 참고 링크는 `./SFR-105_BE_다중게시판.md`, `./SFR-104_AI자동답변.md` 등 실제 파일명과 일부 다르다. 실제 파일은 `SFR-105_BE_다중게시판.md`, `SFR-108_BE_OAuth인증.md` 형태이며, SFR-104 파일은 현재 `docs/sdd/srs_p1`에 없다.

권장 보정:
- 존재하는 파일명 기준으로 링크 정리
- 아직 없는 상세 문서는 "작성 예정"으로 표기

## 누락 보완 체크리스트

- [ ] SFR-101 범위에 파일 첨부/file_map을 다시 포함
- [ ] 업로드 API 경로를 `SRS_P1` 최신 규칙으로 통일
- [ ] 목록/단건/댓글 목록 읽기에서 `read_yn`/`guest_read_yn` 분기 명시
- [ ] Phase 1 ADMIN 활성 여부 확정
- [ ] 공지 작성 시 `board.notice_yn` 검증 추가
- [ ] PostHistory INSERT Phase 확정
- [ ] 댓글 수정/삭제 시 path `post_id`와 `comment.post_id` 일치 검증 추가
- [ ] 답글/대댓글 parent 존재, 소속, depth 검증 추가
- [ ] 게시글 상세 응답에 `files[]` 포함
- [ ] AI 시드 계정 ID를 `USR_00000000`으로 전체 문서 통일

## 권장 수정 방향

SFR-101은 "게시글/댓글 CRUD만" 문서로 두기보다, 상위 SRS가 정의한 **게시판 CRUD + 첨부 매핑의 서버 구현 단위**로 맞추는 것이 좋다. `core/files` 구현이 아직 없더라도 SRS_P1에는 이미 파일 업로드/서빙 공통 규칙이 있으므로, SFR-101에서는 최소한 `file_ids` 수신, `file_map` 생성/해제, 게시판 첨부 정책 검증, 상세 응답 파일 조회까지 포함해야 한다.

반대로 파일 첨부를 정말 제외하려면 상위 문서의 SFR-101 명칭과 Phase 1 범위를 먼저 수정해야 한다. 현재 기준 문서 체계에서는 제외보다 포함이 더 일관된 방향이다.
