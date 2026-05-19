# SFR-101_BE_게시판CRUD 3차 재리뷰 - Codex

| 항목 | 내용 |
|------|------|
| 리뷰 대상 | `docs/sdd/srs_p1/SFR-101_BE_게시판CRUD.md` |
| 관련 확인 | `docs/specs/srs/SRS_P1.md`, `docs/specs/04_Domain.md`, `docs/specs/02_SRS.md`, `docs/sdd/srs_p1/SFR-105_BE_다중게시판.md` |
| 리뷰 일자 | 2026-04-29 |
| 리뷰어 | Codex |

## 총평

직전 2차 재리뷰의 핵심 이슈는 대부분 반영되었다.

- 삭제된 `com_tn_file`을 게시글 수정에서 복원하지 않도록 정리됨
- `file_ids` 존재/삭제 여부와 소유권 검증이 작성 흐름에 추가됨
- `FILE_NOT_FOUND`, `FILE_ACCESS_FORBIDDEN` 에러가 추가됨
- Domain의 AI 시드 계정 ID가 `USR_00000000`으로 정리됨
- Domain의 파일 API 경로가 `POST /api/v1/boards/{board_code}/uploads`, `GET /files/{uuid}` 기준으로 보정됨
- ADMIN/SYSTEM_ADMIN Phase 표기도 SRS_P1과 맞춰짐

현재 SFR-101은 구현 기준 문서로 사용 가능한 수준이다. 남은 항목은 대부분 세부 정책/트랜잭션 안정성 보완이다.

## 남은 발견 사항

### 1. [높음] 게시글 수정 시 `file_ids` 검증이 작성 흐름보다 약함

작성 흐름은 `file_id` 존재, `del_yn=false`, 소유권, `attach_yn`, 개수/크기/확장자 검증을 모두 명시한다. 반면 수정 흐름은 `file_ids` 전달 시 `com_tn_file` 존재와 `del_yn=false`만 확인한다고 되어 있다.

수정에서도 새 첨부 목록을 최종 목록으로 교체하므로 작성과 동일한 검증이 필요하다.

권장 수정:
- 수정 흐름 8단계에 "작성 흐름과 동일한 파일 검증 수행"을 명시
- 특히 `file.created_by == payload["sub"] 또는 ADMIN`, `attach_yn`, `attach_count`, `attach_size`, `attach_ext`를 포함

### 2. [높음] 파일 교체 순서는 검증 후 변경이어야 함

현재 수정 흐름은 "기존 file_map Soft Delete → 새 file_ids 검증/업서트" 순서로 읽힌다. 새 파일 검증이 중간에 실패하면 기존 첨부가 이미 제거된 상태가 될 수 있다. 실제 구현에서 트랜잭션으로 묶으면 롤백되겠지만, 문서에는 순서와 트랜잭션 보장이 명확하지 않다.

권장 수정:
- `file_ids` 전체 검증을 먼저 수행
- 같은 DB 트랜잭션 안에서 PostHistory INSERT, post UPDATE, 기존 file_map soft delete, 새 file_map upsert를 처리
- 실패 시 전체 롤백 명시

### 3. [중간] 댓글 삭제 시 대댓글 처리 정책이 아직 모호함

댓글 목록은 root 댓글을 먼저 조회하고, 해당 root의 replies를 붙이는 구조다. 이 상태에서 root 댓글만 soft delete하면 그 아래 대댓글은 `del_yn=false`여도 목록에서 보이지 않는다. 그런데 `comment_count`는 root 댓글 1건만 감소하면 실제 노출 댓글 수와 캐시가 불일치할 수 있다.

정책 선택이 필요하다.

- 선택 A: root 삭제 시 하위 대댓글도 함께 soft delete하고 `comment_count`를 삭제된 전체 수만큼 감소
- 선택 B: root는 "삭제된 댓글입니다" placeholder로 노출하고 replies는 유지
- 선택 C: 대댓글이 있는 root 댓글은 삭제 제한 또는 관리자만 완전 삭제

Phase 1에서는 A 또는 B 중 하나를 명시하는 것이 구현이 단순하다.

### 4. [중간] 상위 `02_SRS.md`에 오래된 파일 업로드 경로가 남아 있음

`SRS_P1`, `SFR-101`, `Domain`은 파일 업로드 경로를 최신화했지만, `docs/specs/02_SRS.md`의 SFR-101 상세에는 아직 `POST /files`가 남아 있다.

권장 수정:
- `02_SRS.md`의 SFR-101 파일 업로드 설명을 `POST /api/v1/boards/{board_code}/uploads`와 `POST /api/v1/uploads` 구조에 맞춰 갱신
- 게시판 첨부와 일반 업로드가 분리된다는 점을 반영

### 5. [중간] 첨부 크기 단위 표현이 Domain과 ERD에서 다름

- `SFR-105`, `ERD`: `attach_size`는 KB, 기본 `10240`
- `Domain`: `attach_size` 설명은 "첨부 최대 크기 MB (기본 10)"

구현은 숫자 컬럼 기준으로 처리하므로 단위 혼선은 버그로 이어질 수 있다. SFR-105/ERD에 맞춰 Domain도 "KB, 기본 10240"으로 통일하는 것을 권장한다.

### 6. [낮음] 파일 중복 ID 처리 정책이 없음

`file_ids`에 같은 ID가 중복으로 들어오면 `attach_count` 계산, `file_map` upsert, 정렬이 애매해질 수 있다.

권장 수정:
- 요청 단계에서 중복 제거 후 처리할지, 중복 입력을 400으로 거부할지 결정
- 단순 구현은 400 `DUPLICATE_FILE_ID` 또는 기존 400 계열 에러 재사용

### 7. [낮음] 테스트 기준에 수정 파일 검증 케이스가 더 필요함

첨부 테스트는 추가됐지만 수정 시나리오의 실패 케이스가 부족하다.

추가 권장:
- 게시글 수정 시 타인 파일 ID 전달 → 403 `FILE_ACCESS_FORBIDDEN`
- 게시글 수정 시 삭제된 파일 전달 → 404 `FILE_NOT_FOUND`
- 게시글 수정 중 파일 검증 실패 시 기존 첨부 유지
- root 댓글 삭제 시 대댓글 처리 정책에 따른 `comment_count` 검증

## 결론

SFR-101의 주요 구조와 이전 리뷰의 핵심 누락은 정리됐다. 구현 전 마지막으로 보완할 부분은 `수정 시 file_ids 검증을 작성과 동일하게 적용`, `파일 교체 트랜잭션/롤백 명시`, `root 댓글 삭제 시 대댓글 처리 정책 확정`, `02_SRS.md`의 오래된 `POST /files` 문구 갱신이다.
