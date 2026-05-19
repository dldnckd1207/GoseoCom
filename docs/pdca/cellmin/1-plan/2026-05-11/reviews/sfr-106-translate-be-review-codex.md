# sfr-106-translate-be Plan 리뷰 - Codex

| 항목 | 내용 |
|------|------|
| 리뷰 대상 | `docs/pdca/cellmin/1-plan/2026-05-11/sfr-106-translate-be.md` |
| 기준 문서/코드 | `apps/server/app/translate/models.py`, `apps/server/app/translate/schemas.py`, `apps/server/app/core/files/*`, `apps/server/alembic/versions/*` |
| 리뷰 일자 | 2026-05-11 |
| 리뷰어 | Codex |

## 총평

Plan 문서는 이미지 1장 업로드부터 OCR, Gemini 번역, 폴링 조회까지 MVP 범위를 명확히 잡고 있다. Phase 2 제외 범위도 분리되어 있어 구현 범위를 좁히는 데 도움이 된다.

다만 현재 서버 코드에는 translate 모델, 일부 schema, ID 시퀀스, 초기 Alembic 테이블 정의가 이미 존재한다. 따라서 Plan의 성공 기준과 범위 표현을 그대로 따르면 구현자가 이미 있는 자산을 중복 생성할 위험이 있다. 파일 저장 방식, 실패/빈 OCR 처리, 오류 코드도 구현 전에 조금 더 구체화하는 편이 안전하다.

## 발견 사항

### High - Alembic 마이그레이션 생성 기준이 현재 코드 상태와 충돌 가능

성공 기준에 `Alembic 마이그레이션 생성 및 적용 완료`가 포함되어 있다.

현재 코드 기준으로는 `ai_tn_book`, `ai_tn_book_page`, `ai_th_pipeline_run` 등이 이미 초기 migration에 포함되어 있고, `BOOK_`, `BPAGE_` 시퀀스도 별도 migration 및 `id_generator`에 존재한다. 이 상태에서 신규 migration을 무조건 생성하면 중복 테이블 또는 중복 시퀀스 작업이 발생할 수 있다.

권장 보완:

- 성공 기준을 `Alembic 마이그레이션 상태 확인 및 누락분 반영`으로 변경
- 구현 전 `alembic current/head`, 실제 DB 테이블 존재 여부 확인을 체크리스트에 추가
- 신규 migration은 누락 컬럼/인덱스/시퀀스가 있을 때만 생성한다고 명시

### High - BackgroundTask 처리의 DB 세션 생명주기 기준이 없음

Plan은 BackgroundTask 비동기 실행을 요구하지만, 요청 스코프의 DB 세션을 그대로 background 작업에 넘길지, 작업 내부에서 새 세션을 열지 기준이 없다. FastAPI 요청이 종료된 뒤 세션을 재사용하면 커밋 실패나 closed session 문제가 생길 수 있다.

권장 보완:

- BackgroundTask는 `book_id` 같은 식별자만 받고, runner 내부에서 새 `AsyncSession`을 생성한다고 명시
- 실패 시 `book.status`, `book_page.status`, `pipeline_run.status/error_msg`를 같은 세션 흐름에서 정리하는 규칙 추가

### Medium - 파일 저장 방식이 기존 FileService와 분리될 수 있음

Plan은 파일 저장을 `./storage/files/`로만 정의한다. 현재 서버에는 `settings.file_local_path` 기반의 `FileService`와 `FILE_` 메타데이터 저장 구조가 있다. 번역 업로드가 기존 파일 서비스를 재사용하지 않으면 파일 경로, 권한, 삭제, 다운로드 정책이 분리된다.

권장 보완:

- 번역 업로드가 기존 `FileService`를 재사용하는지 명시
- 독립 저장이라면 Book/Page에 원본 파일 경로 또는 파일 ID를 어떻게 연결할지 정의
- 설정값은 하드코딩 경로가 아니라 `settings.file_local_path` 기준으로 표현

### Medium - 업로드 검증 실패 응답이 정의되지 않음

`image/*`, 최대 10MB 제한은 요구사항에 있으나 실패 시 HTTP status, error code, 검증 기준이 없다.

권장 보완:

- MIME 검증 실패: 예) `400 INVALID_IMAGE_TYPE`
- 크기 초과: 예) `400 IMAGE_SIZE_EXCEEDED`
- `content_type`만 볼지, 확장자/파일 시그니처까지 확인할지 결정

### Medium - OCR 텍스트 없음 처리 정책이 사용자 관점에서 모호함

`OCR 텍스트가 없으면 번역 건너뜀 -> COMPLETED 처리`는 기술적으로 단순하지만, 사용자는 성공으로 오해할 수 있다. OCR 실패와 정상적으로 텍스트가 없는 이미지가 구분되지 않는다.

권장 보완:

- `book.status = COMPLETED`를 유지하더라도 `book_page.status` 또는 `pipeline_run.error_msg`/별도 message에 `NO_TEXT_DETECTED` 기록
- GET 응답에서 OCR 텍스트 없음 상태를 클라이언트가 표시할 수 있도록 상태 또는 메시지 필드 추가 검토

### Low - 외부 API 설정 누락 시 기대 동작이 Plan에 없음

Google Vision 또는 Gemini API 키가 없을 때 실패 처리 기준은 Design에만 있고 Plan에는 없다. 운영/테스트 기준에서는 중요한 실패 경로다.

권장 보완:

- 설정 누락 시 `FAILED` 처리 및 `pipeline_run.error_msg` 저장을 Plan의 비즈니스 규칙에 추가
- 외부 API 호출 mock 테스트를 성공 기준에 포함

## 확인 완료 항목

- 이미지 1장 MVP 범위는 Phase 2 제외 범위와 잘 분리되어 있음
- 본인 소유 Book만 조회 가능하다는 접근 제어 요구사항은 적절함
- 202 응답 후 폴링 조회 방식은 외부 OCR/LLM 지연을 고려하면 타당함
- 직역/의역 분리 저장 요구는 기존 `BookPage` 모델의 필드와 맞음

## 권장 보완

- 마이그레이션 성공 기준을 “신규 생성”이 아닌 “현재 상태 검증 및 누락 반영”으로 수정
- BackgroundTask 내부 DB 세션 생성 원칙 추가
- 파일 저장은 기존 `FileService` 재사용 여부를 확정
- 업로드 검증 실패 응답 코드 정의
- OCR 결과 없음 상태를 사용자에게 노출할 수 있는 방식 정의

## 결론

Plan의 MVP 범위는 적절하다. 다만 현재 코드베이스에 이미 존재하는 translate DB/스키마/시퀀스 자산을 고려해, “신규 생성” 중심 표현을 “기존 자산 확인 후 누락 구현”으로 조정하는 것이 필요하다. BackgroundTask 세션과 파일 저장 정책도 구현 전 확정하는 것을 권장한다.

## 추가 확인 - 2026-05-14

2026-05-13 수정본 기준으로 최초 리뷰의 주요 지적은 대부분 반영되었다.

반영 확인:

- `updated: 2026-05-13` 메타데이터가 추가됨
- 파일 저장이 기존 `FileService` 재사용 및 `settings.file_local_path` 기준으로 정리됨
- BackgroundTask runner가 `book_id`, `file_local_path`만 받고 내부에서 새 `AsyncSession`을 생성한다는 원칙이 추가됨
- 업로드 MIME 타입/크기 오류 코드가 `INVALID_IMAGE_TYPE`, `IMAGE_SIZE_EXCEEDED`로 정의됨
- OCR 텍스트 없음, 외부 API 키 미설정 실패 처리가 비즈니스 규칙에 추가됨
- 성공 기준이 신규 migration 생성이 아니라 기존 DB/시퀀스 상태 확인으로 변경됨
- 내 번역 목록 API가 범위와 성공 기준에 추가됨

남은 확인 사항:

### Medium - `NO_TEXT` 상태값을 공식 상태 목록에 추가 필요

Plan은 OCR 텍스트가 없으면 `book_page.status = NO_TEXT`로 처리한다고 정의한다. 현재 모델은 문자열 필드라 저장 자체는 가능하지만, 기존 주석과 상태 흐름에는 `NO_TEXT`가 포함되어 있지 않다.

권장 보완:

- `BookPage.status` 허용 상태 목록에 `NO_TEXT`를 명시
- GET 응답에서 `NO_TEXT`를 클라이언트가 별도 empty state로 처리해야 함을 추가

### Low - 목록 API status 필터 오류 기준 보강 권장

`GET /api/v1/translate` 목록 API가 추가되었지만, 허용되지 않는 `status` 값이 들어왔을 때의 응답 기준은 Plan에 없다.

권장 보완:

- 잘못된 status 필터는 `400 INVALID_STATUS` 또는 FastAPI/Pydantic `422` 중 하나로 확정
- 성공 기준에 status 필터 정상/오류 케이스를 함께 추가

### Low - 타인 목록 조회 방지 기준은 암묵적임

목록 조회는 “본인 소유 Book만 허용”으로 정리되어 있어 방향은 맞다. 다만 목록 API는 특정 `book_id`가 없으므로 403보다는 repository query에서 `owner_user_id = payload["sub"]` 조건을 반드시 적용하는 방식이 핵심이다.

권장 보완:

- 목록 repository 조건에 `owner_user_id` 필터가 필수임을 설계 문서와 함께 명시

## 추가 결론 - 2026-05-14

Plan은 최초 리뷰 대비 상당히 안정화되었다. 구현 전에는 `NO_TEXT` 상태값의 공식화와 목록 API status 필터 오류 기준만 추가로 정리하면 충분하다.

## 추가 확인 2 - 2026-05-14

수정본 재확인 결과, Design에는 `pipeline_run_id` 전달 방식이 반영되었지만 Plan의 BackgroundTask 설명은 아직 이전 형태로 남아 있다.

### Medium - Plan과 Design의 runner 인자 불일치

Plan은 BackgroundTask runner가 `book_id`와 `file_local_path`만 받는다고 정의한다. 반면 Design은 `run_pipeline(book_id, file_local_path, pipeline_run_id)` 형태로 수정되어 있다.

이 불일치가 남아 있으면 구현자가 `PipelineRun`을 어떤 기준으로 갱신해야 하는지 다시 애매해질 수 있다.

권장 보완:

- Plan의 비즈니스 규칙을 `book_id`, `file_local_path`, `pipeline_run_id`를 전달한다고 수정
- 파이프라인 실패 시 `pipeline_run_id`로 대상 row를 갱신한다고 명시

## 추가 결론 2 - 2026-05-14

Plan은 Design과 맞춰 runner 인자만 보정하면 된다. 특히 `pipeline_run_id` 전달은 PipelineRun 상태 갱신의 기준이므로 Plan에도 명시하는 것을 권장한다.

## 추가 확인 3 - 2026-05-14: 파일 업로드/번역 요청 API 분리

Design이 파일 업로드와 번역 요청을 분리하는 2단계 흐름으로 변경되었다.

```text
1. POST /api/v1/files -> file_id
2. POST /api/v1/translate { file_id } -> 202 book_id
```

이 방향은 번역 API가 multipart 처리와 pipeline 시작을 동시에 책임지지 않아도 되므로 구조적으로 더 단순하다. 다만 Plan에는 아직 이전 “이미지 업로드 + 파이프라인 시작” 표현이 일부 남아 있어 Design과 불일치한다.

### High - Plan의 translate API 설명이 2단계 흐름과 불일치

Plan의 포함 범위는 `POST /api/v1/translate — 이미지 업로드 + 파이프라인 시작`으로 되어 있다. 그러나 Design은 `POST /api/v1/translate`가 이미지를 직접 받지 않고 `file_id`를 JSON body로 받는 것으로 변경되었다.

권장 보완:

- Plan 포함 범위에 `POST /api/v1/files — 이미지 선업로드`를 추가
- `POST /api/v1/translate` 설명을 `file_id 기반 파이프라인 시작 (202)`으로 수정
- 성공 기준도 `파일 업로드 -> file_id 반환 -> 번역 요청 -> book_id 반환` 흐름으로 수정

### Medium - 목록 API 경로가 Plan 내부에서 불일치

Plan 포함 범위에는 `POST /api/v1/translate/list`가 적혀 있지만, 성공 기준에는 아직 `GET /api/v1/translate`가 남아 있다.

권장 보완:

- 성공 기준을 `POST /api/v1/translate/list -> 페이지네이션 목록 반환`으로 수정
- Design과 동일하게 request body 기반 목록 조회임을 명시

### Medium - 10MB 제한의 책임 위치를 Plan에 명시 필요

파일 업로드와 번역 요청이 분리되면 `image/*`, 10MB 제한을 어느 단계에서 검증하는지 명확해야 한다. 업로드 API에서 1차 검증하더라도, 번역 요청 시 `File.file_size` 기준으로 재검증하는 편이 안전하다.

권장 보완:

- 파일 업로드 API에서 `image/*`, 10MB 검증
- 번역 요청 시 `file_id`로 조회한 `File.mime_type`, `File.file_size`를 재검증
- 크기 초과 시 `400 IMAGE_SIZE_EXCEEDED`

## 추가 결론 3 - 2026-05-14

2단계 API 구조는 적절하다. Plan은 Design 변경에 맞춰 `POST /api/v1/translate`의 역할을 “업로드”가 아니라 “file_id 기반 번역 요청”으로 수정하고, 목록 API 경로와 파일 크기 검증 책임을 정리하면 된다.

## 추가 확인 4 - 2026-05-14

수정본에서 Plan은 업로드 API를 `POST /api/v1/uploads` 신규 구현으로 정리했고, 번역 요청은 `file_id` 기반으로 변경되었다. 파일 소유권, MIME, 크기 재검증도 Plan 비즈니스 규칙에 추가되어 방향은 적절하다.

남은 발견 사항:

### High - Design과 업로드 API 경로가 불일치

Plan은 업로드 API를 `POST /api/v1/uploads`로 정의한다. 반면 Design은 여전히 `POST /api/v1/files`를 기존 엔드포인트로 사용한다고 되어 있다.

권장 보완:

- 업로드 API 경로를 하나로 통일
- Plan 기준을 채택한다면 Design의 `/api/v1/files` 표현을 모두 `/api/v1/uploads`로 수정
- `POST /api/v1/uploads`가 신규 구현 범위임을 Design에도 명시

### Medium - 성공 기준의 목록 API 경로가 포함 범위와 불일치

Plan 포함 범위에는 `POST /api/v1/translate/list`가 명시되어 있지만, 성공 기준에는 아직 `GET /api/v1/translate`가 남아 있다.

권장 보완:

- 성공 기준을 `POST /api/v1/translate/list -> 페이지네이션 목록 반환`으로 수정

### Low - Plan updated 메타데이터 보정 권장

Plan 본문은 2026-05-14 변경 내용을 반영하고 있지만 front matter의 `updated` 값은 아직 `2026-05-13`이다.

권장 보완:

- `updated: 2026-05-14`로 수정

## 추가 결론 4 - 2026-05-14

Plan은 API 분리 방향을 거의 반영했다. 남은 작업은 Design과 업로드 API 경로를 통일하고, 성공 기준의 목록 API 경로와 `updated` 메타데이터를 보정하는 것이다.
