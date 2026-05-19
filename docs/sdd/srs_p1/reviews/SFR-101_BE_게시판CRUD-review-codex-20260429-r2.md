# SFR-101_BE_게시판CRUD 2차 재리뷰 - Codex

| 항목 | 내용 |
|------|------|
| 리뷰 대상 | `docs/sdd/srs_p1/SFR-101_BE_게시판CRUD.md` |
| 관련 확인 | `docs/specs/srs/SRS_P1.md`, `docs/specs/04_Domain.md`, `docs/specs/05_ERD.md` |
| 리뷰 일자 | 2026-04-29 |
| 리뷰어 | Codex |

## 총평

직전 재리뷰에서 남긴 핵심 이슈는 대부분 해소되었다.

- `파일 첨부 Phase 1 제외` 잔존 문구가 제거되고 Phase 1 포함으로 정리됨
- `file_ids`가 작성/수정 요청 스키마에 추가됨
- 업로드 API가 `POST /api/v1/boards/{board_code}/uploads`로 SFR-101/SRS_P1 간 통일됨
- `attach_yn`, 첨부 개수/크기/확장자 에러 코드가 추가됨
- PostHistory Phase 정책은 Domain 일부까지 반영됨

현재 SFR-101 자체는 구현 착수 가능한 수준에 가깝다. 다만 파일 보안/수명주기 정책과 Domain 문서 잔여 불일치가 남아 있다.

## 남은 발견 사항

### 1. [높음] `com_tn_file.del_yn=true` 파일을 게시글 수정에서 복원하는 정책은 위험함

- 대상: `SFR-101_BE_게시판CRUD.md` 게시글 수정 흐름, 요청 스키마 설명, 결정 사항의 `파일 수정 정책`
- 현재 내용: 새 `file_ids` 각각에 대해 `com_tn_file.del_yn=true`이면 복원

`com_tn_file.del_yn=true`는 파일 엔티티 자체가 삭제된 상태를 의미한다. 게시글 수정 요청이 삭제된 파일을 조용히 복원하면, 사용자가 삭제한 파일이나 다른 엔티티에서 제거된 파일이 다시 노출될 수 있다. `file_map`의 soft delete 복원과 `file` 자체 복원은 다른 문제다.

권장 수정:
- `com_tn_file.del_yn=true` 파일은 404 또는 400으로 거부
- 복원 대상은 기존 `(file_id, target_type=POST, target_id=post_id)`의 `file_map.del_yn=true` row에 한정
- 결정 사항 문구를 "`file_map`은 upsert/복원, `com_tn_file.del_yn=true` 파일은 사용 불가"로 수정

### 2. [높음] `file_ids` 소유권/업로드 컨텍스트 검증이 명시되지 않음

- 대상: 게시글 작성/수정 첨부 정책 검증 단계

현재는 `file_ids`의 확장자/크기/개수만 검증한다. 하지만 사용자가 임의의 `FILE_...` 값을 전달할 수 있다면, 다른 사용자가 업로드한 파일을 자신의 게시글에 연결할 수 있다.

권장 수정:
- 각 `file_id`가 존재하고 `del_yn=false`인지 확인
- `file.created_by == current_user.id` 또는 관리자 권한인지 확인
- 이미 다른 민감한 target(`BOOK` 등)에 연결된 파일을 재사용할 수 있는지 정책 확정
- 실패 에러 예: `FILE_NOT_FOUND`, `FILE_ACCESS_FORBIDDEN`

### 3. [중간] 첨부 파일 타입 정책이 상위 문서와 아직 흔들림

- `02_SRS.md`: 파일 검증은 이미지 타입만 허용, 최대 10MB
- `04_Domain.md`: MIME 타입 `image/*`
- `SFR-101`: 예시 응답에 `첨부파일.pdf`, `file_ext: pdf`
- `SFR-105`: 게시판 설정 예시에 `jpg,png,pdf`가 있음

게시판 첨부가 이미지 전용인지, 게시판 설정이 허용하면 PDF도 가능한지 확정이 필요하다. SFR-101이 게시판 정책을 따르는 방향이면 상위 SRS/Domain의 "이미지 타입만" 문구를 완화해야 한다. 반대로 Phase 1 이미지 전용이면 SFR-101/SFR-105 예시의 `pdf`를 제거해야 한다.

### 4. [중간] Domain 문서에 `USER_00000000`이 아직 남아 있음

- `SFR-101`, `SRS_P1`, `ERD`: `USR_00000000`
- `04_Domain.md`: 용어집, User 설명, UBR-06, BBR-03, 통합 규칙에 `USER_00000000` 잔존

SFR-101에서는 `USR_00000000`으로 확정했으므로 Domain도 모두 `USR_00000000`으로 통일해야 한다.

### 5. [중간] Domain 문서의 파일 API 경로가 SRS_P1과 불일치함

- `SRS_P1`: `POST /api/v1/uploads`, `GET /files/{uuid}`
- `SFR-101`: `POST /api/v1/boards/{board_code}/uploads`
- `04_Domain.md`: `POST /files`, `GET /files/:id`

Domain의 FBR-01/FBR-06이 오래된 경로로 보인다. 구현 기준을 SRS_P1/SFR-101로 둘 거라면 Domain도 최신 경로로 갱신하는 것이 좋다.

### 6. [낮음] ADMIN Phase 표기가 SRS_P1과 Domain에서 다름

- `SRS_P1`: ADMIN/SYSTEM_ADMIN 역할은 Phase 1부터 활성, Admin UI만 Phase 3
- `04_Domain.md`: UserLevel enum에서 ADMIN/SYSTEM_ADMIN Phase가 3

권한 레벨 자체를 Phase 1에 활성화하기로 정리했으므로 Domain의 Phase 표기도 "1, UI는 3" 형태로 맞추는 편이 좋다.

### 7. [낮음] 테스트 기준이 새 첨부 정책을 따라가지 못함

SFR-101의 정상/예외 테스트 기준에는 아직 파일 첨부 관련 케이스가 없다.

추가 권장:
- 게시글 작성 시 `file_ids` 전달 → `file_map` 생성
- 게시글 수정 시 `file_ids` 전체 교체 → 기존 mapping soft delete, 새 mapping 생성/복원
- `attach_yn=false` 게시판에 파일 첨부 → `ATTACH_NOT_ALLOWED`
- 첨부 개수/크기/확장자 위반
- 타인 파일 ID 첨부 시도 차단

## 결론

SFR-101 문서의 주요 구조는 이제 적절하다. 남은 핵심 보완은 `file` 자체 복원 정책 제거, `file_ids` 소유권 검증 추가, Domain 문서의 `USR_00000000`/파일 API 경로 동기화다. 이 세 가지를 정리하면 SFR-101은 구현 기준 문서로 사용해도 무리가 크지 않다.
