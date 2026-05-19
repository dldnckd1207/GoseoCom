# sfr-106-translate-be Design 리뷰 - Codex

| 항목 | 내용 |
|------|------|
| 리뷰 대상 | `docs/pdca/cellmin/2-design/2026-05-11/sfr-106-translate-be.md` |
| 기준 문서/코드 | `docs/pdca/cellmin/1-plan/2026-05-11/sfr-106-translate-be.md`, `apps/server/app/translate/*`, `apps/server/app/core/files/*`, `apps/server/app/core/common/id_generator.py`, `apps/server/alembic/versions/*` |
| 리뷰 일자 | 2026-05-11 |
| 리뷰어 | Codex |

## 총평

Design 문서는 Router, Service, Repository, Pipeline 모듈을 나누고 OCR/번역 단계를 순차 처리하는 구조를 제시한다. API 응답 형태도 기존 `ApiResponse` 포맷과 대체로 맞고, 단일 이미지 MVP에 필요한 주요 endpoint가 정리되어 있다.

다만 현재 코드베이스에는 `translate/models.py`, `translate/schemas.py`, Alembic 초기 테이블, `BOOK_`/`BPAGE_` 시퀀스가 이미 존재한다. 문서의 “신규” 또는 “마이그레이션 생성” 표현은 실제 구현 시 중복 작업을 유발할 수 있다. 또한 BackgroundTask의 DB 세션 관리, 업로드 파일과 BookPage의 연결, Gemini 응답 파싱 규칙이 빠져 있어 구현자가 서로 다른 방식으로 해석할 여지가 있다.

## 발견 사항

### High - DB 마이그레이션 생성 지시가 중복 테이블 생성으로 이어질 수 있음

문서는 `models.py`에 이미 정의된 4개 테이블에 대한 Alembic 마이그레이션 생성을 지시한다.

현재 서버 코드 기준으로 `ai_tn_book`, `ai_tn_book_page`, `ai_th_page_revision`, `ai_th_pipeline_run`은 초기 migration에 이미 포함되어 있다. 이 문장 그대로 신규 migration을 만들면 테이블 중복 생성 위험이 있다.

권장 보완:

- “마이그레이션 생성”을 “기존 migration 및 실제 DB 반영 여부 확인”으로 변경
- 누락된 테이블/컬럼/인덱스가 있을 때만 보정 migration을 생성한다고 명시
- PageRevision은 Phase 2라면 이번 SFR에서 검증만 할지, 실제 migration 대상인지 분리

### High - 시퀀스 추가 설명이 현재 코드와 맞지 않음

`BOOK_`, `BPAGE_` 시퀀스를 기존 `add_id_sequences` migration에 추가하거나 신규 migration으로 만든다고 되어 있다. 현재 `apps/server/app/core/common/id_generator.py`와 `4ad5979b5ce1_add_id_sequences.py`에는 이미 `seq_book`, `seq_bpage`가 정의되어 있다.

권장 보완:

- 시퀀스는 “이미 정의되어 있으므로 동작 확인”으로 수정
- `next_id("BOOK_", db)`, `next_id("BPAGE_", db)` 사용을 구현 기준으로 명시
- 실제 DB에 시퀀스가 없을 경우에만 보정 migration 생성

### High - BackgroundTask runner의 DB 세션 생성 방식이 빠져 있음

`run_pipeline(book_id: str)` 흐름은 단계는 명확하지만, runner가 DB 세션을 어디서 얻는지 정의하지 않는다. 요청 스코프의 `AsyncSession`을 BackgroundTask에 전달하면 요청 종료 후 세션이 닫혀 실패할 수 있다.

권장 보완:

```python
async def run_pipeline(book_id: str) -> None:
    async with async_session() as db:
        ...
```

또는 프로젝트의 세션 팩토리 이름에 맞춰 runner 내부 세션 생성 규칙을 문서화한다. BackgroundTask에는 `book_id`와 필요한 최소 식별자만 전달하는 것이 좋다.

### High - 업로드 파일과 pipeline 입력 파일의 연결 모델이 불명확함

Pipeline 흐름에는 `local_path로 이미지 읽기`가 있지만, `Book` 또는 `BookPage` 모델에는 현재 원본 파일 경로 필드가 없다. 기존 `FileService`를 사용한다면 `FILE_` 메타데이터와 Book/Page를 어떻게 연결할지, 독립 저장이라면 경로를 어디에 저장할지 정의가 필요하다.

권장 보완:

- 옵션 A: 기존 `FileService`로 저장하고, `BookPage` 또는 별도 매핑에 `file_id` 연결
- 옵션 B: translate 전용 저장 경로를 만들고, `BookPage`에 원본 경로 컬럼을 추가하는 migration 포함
- 옵션 C: Book 생성 직후 background task에는 임시 저장 경로를 넘기고, DB에는 원본 파일 추적을 하지 않는다고 명시

현재 설계만으로는 background runner가 `book_id`만 받아 파일을 찾을 방법이 부족하다.

### Medium - `schemas.py (신규)` 표현이 실제 파일 상태와 다름

파일 구조에서 `schemas.py`를 신규로 표시하지만, 현재 `apps/server/app/translate/schemas.py`는 이미 존재한다.

권장 보완:

- `schemas.py (기존 - 필요 시 확장)`으로 수정
- 현재 schema 필드와 API 명세가 일치하는지 검증 항목 추가

### Medium - Gemini 응답 파싱 실패 기준이 없음

Design은 Gemini가 `literal_text`, `interpretive_text`를 반환한다고 가정하지만, LLM 응답은 자유 텍스트로 흔들릴 수 있다. JSON 파싱 실패, 한쪽 필드 누락, 안전 필터 차단 시 처리 기준이 필요하다.

권장 보완:

- Gemini 프롬프트는 JSON object만 반환하도록 명시
- 응답 schema 예시 추가
- 파싱 실패 시 1회 재시도 후 `FAILED` 처리 또는 원문 응답을 `error_msg`에 요약 저장

예시:

```json
{
  "literal_text": "...",
  "interpretive_text": "..."
}
```

### Medium - 상태 전이와 PipelineRun 기록 시점이 부족함

Pipeline 흐름은 book 상태만 주로 다룬다. `PipelineRun`은 요구사항에 포함되어 있지만 생성 시점, `RUNNING`, `COMPLETED`, `FAILED`, `duration_ms`, `success_cnt`, `fail_cnt` 기록 기준이 구체적이지 않다.

권장 보완:

- POST 요청 시 `PipelineRun(PENDING)` 생성 여부
- runner 시작 시 `RUNNING`, `started_at`
- 성공 시 `COMPLETED`, `completed_at`, `duration_ms`, `total_cnt=1`, `success_cnt=1`
- 실패 시 `FAILED`, `fail_cnt=1`, `error_msg`, 필요 시 `error_stack`

### Medium - 업로드 검증과 오류 응답 명세가 누락됨

Plan에는 `image/*`, 10MB 제한이 있으나 Design의 API 명세에는 성공 응답만 있다.

권장 보완:

- 400 `INVALID_IMAGE_TYPE`
- 400 `IMAGE_SIZE_EXCEEDED`
- 401 `UNAUTHORIZED`
- 403 `FORBIDDEN`
- 외부 API 설정 누락 시 GET 결과에서 `FAILED`와 error message 확인 가능

### Low - 테스트 전략에서 BackgroundTask 실행 방식이 모호함

통합 테스트는 `POST -> 202`, `GET` 폴링 시뮬레이션을 제시한다. 하지만 FastAPI BackgroundTask가 테스트 클라이언트에서 언제 실행되는지, OCR/번역 mock을 어디에 주입하는지 명확하지 않다.

권장 보완:

- service 또는 runner에 OCR/translator 함수를 주입 가능하게 설계
- 테스트에서는 runner를 직접 호출하는 단위 테스트와 API 202 응답 테스트를 분리
- 실패 케이스: OCR 예외, Gemini 예외, 빈 OCR, 타인 조회 403 포함

## 확인 완료 항목

- API 응답 wrapper는 기존 `ApiResponse` 구조와 대체로 일치
- `BookPage` 모델은 `ocr_text`, `literal_text`, `interpretive_text`, `ocr_engine`, `translator_engine`, `status` 필드를 이미 가지고 있어 결과 저장 요구와 맞음
- `Book.status`의 `PENDING`, `OCR_PROCESSING`, `TRANSLATING`, `COMPLETED`, `FAILED` 상태는 문서의 pipeline 단계와 맞음
- `PipelineRun` 모델은 실패 이력 저장 요구를 수용할 수 있는 필드를 가지고 있음

## 권장 보완

- DB/시퀀스는 신규 생성이 아니라 현재 반영 여부 검증으로 설계 수정
- BackgroundTask runner 내부 DB 세션 생성 규칙 명시
- `book_id`만으로 원본 이미지 경로를 찾는 방식을 구체화
- Gemini 응답 JSON schema와 파싱 실패 처리 추가
- PipelineRun 생성/상태 전이/카운트 기록 기준 추가
- 업로드 검증 실패 응답과 테스트 케이스 보강

## 결론

Design의 레이어 구조와 API 방향은 적절하다. 구현 전에는 현재 코드에 이미 존재하는 translate DB 자산을 반영해 문서를 보정하고, BackgroundTask 세션 관리와 파일 경로 추적 방식을 확정해야 한다. 이 두 가지가 정리되지 않으면 pipeline 구현 시 런타임 실패나 데이터 추적 누락이 발생할 가능성이 높다.

## 추가 확인 - 2026-05-14

2026-05-13 수정본 기준으로 최초 리뷰의 주요 지적은 대부분 반영되었다.

반영 확인:

- `schemas.py`가 신규가 아니라 기존 확장 대상으로 수정됨
- DB/시퀀스 섹션이 신규 migration 생성이 아니라 기존 반영 상태 확인으로 변경됨
- `next_id("BOOK_", db)`, `next_id("BPAGE_", db)` 사용 기준이 명시됨
- POST/GET 상세 외에 `GET /api/v1/translate` 목록 API가 추가됨
- BackgroundTask runner가 자체 `AsyncSession`을 생성하는 구조가 아키텍처와 pipeline 흐름에 반영됨
- PipelineRun 생명주기 표가 추가되어 `PENDING`, `RUNNING`, `COMPLETED`, `FAILED` 기록 시점이 명확해짐
- Gemini JSON 응답 규칙과 파싱 실패 시 1회 재시도 후 `FAILED` 처리 기준이 추가됨
- 테스트 전략에 OCR 빈 텍스트, OCR 예외, Gemini 예외/파싱 실패, 권한, 업로드 검증 케이스가 추가됨
- 외부 의존성이 이미 설치됨으로 정리됨

남은 발견 사항:

### High - `FileUploadResponse.local_path`는 현재 존재하지 않음

파일 저장 및 Pipeline 입력 섹션은 `FileService.upload(image, user_id)` 호출 후 `FileUploadResponse`에서 `file_local_path`를 추출한다고 설명한다. 예시 코드도 다음처럼 되어 있다.

```python
file_resp = await file_service.upload(image, user_id)
background_tasks.add_task(run_pipeline, book_id, file_resp.local_path)
```

하지만 현재 `apps/server/app/core/files/schemas.py`의 `FileUploadResponse`에는 `local_path` 필드가 없다. 실제 반환 필드는 `file_id`, `original_name`, `url_path`, `file_size`, `file_ext`이다. 그대로 구현하면 타입 오류 또는 런타임 오류가 발생한다.

권장 보완:

- 내부 service 용도로 `FileUploadResponse`에 `local_path`를 추가할지 결정
- 또는 `FileService.upload()`가 `File` 엔티티/별도 내부 DTO를 반환하도록 분리
- 또는 `file_id`를 받은 뒤 repository에서 `File.local_path`를 조회해 runner에 넘기도록 설계 수정

### High - runner가 갱신할 `PipelineRun` 식별 방식이 불명확함

PipelineRun 생명주기에는 POST 요청 처리 시 `PENDING` run을 생성한다고 되어 있다. 그러나 `run_pipeline()` 시그니처는 `book_id`, `file_local_path`만 받는다. runner가 어떤 PipelineRun row를 `RUNNING`/`COMPLETED`/`FAILED`로 갱신해야 하는지 애매하다.

권장 보완:

- POST 요청 시 생성한 `pipeline_run_id`를 `run_pipeline(book_id, file_local_path, pipeline_run_id)`로 전달
- 또는 runner 시작 시 `book_id` 기준 최신 `PENDING` run을 조회한다고 명시

첫 번째 방식이 동시 실행과 재시도 상황에서 더 명확하다.

### Medium - `NO_TEXT` page status의 허용 상태 목록 보강 필요

Pipeline 흐름에는 OCR 텍스트가 없을 때 `book_page.status = NO_TEXT`로 처리한다고 되어 있다. 현재 모델 주석과 API 예시에는 `PENDING`, `COMPLETED` 등의 일반 상태만 보인다.

권장 보완:

- `BookPage.status` 상태 목록에 `NO_TEXT`를 추가
- GET 상세 응답 예시에 `NO_TEXT` 케이스를 하나 더 추가하거나 별도 설명 추가

### Medium - 목록 API status 필터 검증 실패 응답 누락

`GET /api/v1/translate`는 `status` 필터 허용값을 적고 있지만, 허용값 외 입력의 응답 기준이 없다.

권장 보완:

- `400 INVALID_STATUS` 또는 Pydantic enum 기반 `422` 중 하나로 확정
- API 테스트에 invalid status 케이스 추가

## 추가 결론 - 2026-05-14

Design은 최초 리뷰 대비 대부분의 구조적 리스크가 해소되었다. 남은 핵심은 `FileUploadResponse.local_path` 가정과 `PipelineRun` 식별 방식이다. 이 두 가지는 구현 시 바로 오류로 이어질 수 있으므로 문서 수정 후 작업하는 것을 권장한다.

## 추가 확인 2 - 2026-05-14

수정본 재확인 결과, `pipeline_run_id`를 runner에 전달하는 방식과 목록 API의 status 필터/owner 조건은 반영되었다. 다만 `FileUploadResponse.local_path` 보완 방식은 현재 공용 API 응답 구조와 충돌할 수 있다.

반영 확인:

- `GET /api/v1/translate` status 필터 허용값 외 입력은 Pydantic Literal 기반 422로 정의됨
- 목록 repository 쿼리에 `owner_user_id = payload["sub"]` 조건 필수가 명시됨
- `BookPageResponse.status`에 `NO_TEXT`가 추가됨
- `run_pipeline(book_id, file_local_path, pipeline_run_id)` 형태로 PipelineRun 갱신 대상이 명확해짐

남은 발견 사항:

### High - `FileUploadResponse.local_path` 추가는 내부 경로 노출 위험이 있음

Design은 현재 `FileUploadResponse`에 `local_path: str` 필드를 추가해 runner에 전달한다고 되어 있다.

그러나 `FileUploadResponse`는 translate 내부 전용 DTO가 아니라 게시판 선업로드 API의 public response model로도 사용된다.

```python
@board_upload_router.post(
    "/{board_code}/uploads",
    response_model=ApiResponse[FileUploadResponse],
)
```

따라서 `FileUploadResponse`에 `local_path`를 추가하면 게시판 업로드 응답에도 서버 내부 파일 경로가 포함될 수 있다. 이는 불필요한 내부 경로 노출이며, 배포 환경의 디렉토리 구조가 API 사용자에게 드러나는 문제가 있다.

권장 보완:

- `FileUploadResponse`는 public API 응답 DTO로 유지하고 `local_path`를 추가하지 않음
- translate service에서 `file_id`로 `File` 엔티티를 repository 조회해 `local_path`를 얻음
- 또는 `FileService.upload()`가 내부용 DTO/엔티티를 반환하고, router에서 public `FileUploadResponse`로 변환하는 방식으로 분리

예시 방향:

```python
file_resp = await file_service.upload(image, user_id)
file_entity = await file_repo.get_by_id(file_resp.file_id)
background_tasks.add_task(run_pipeline, book_id, file_entity.local_path, pipeline_run.id)
```

### Medium - Plan과 Design의 runner 인자 불일치

Design은 `pipeline_run_id` 전달 방식으로 수정되었지만, Plan에는 runner가 `book_id`, `file_local_path`만 받는다고 남아 있다.

권장 보완:

- Plan도 `book_id`, `file_local_path`, `pipeline_run_id`를 전달한다고 맞춤
- 두 문서 모두 PipelineRun 갱신 기준을 `pipeline_run_id`로 통일

## 추가 결론 2 - 2026-05-14

Design은 `pipeline_run_id` 문제는 해소되었지만, `FileUploadResponse`에 `local_path`를 추가하는 방식은 피하는 것이 좋다. 공용 응답 DTO와 내부 처리용 데이터를 분리하거나, 업로드 후 `file_id`로 `File.local_path`를 조회하는 설계로 수정하는 것을 권장한다.

## 추가 확인 3 - 2026-05-14: 파일 업로드/번역 요청 API 분리

수정본은 파일 업로드와 번역 요청을 분리하는 2단계 흐름으로 변경되었다.

```text
1. POST /api/v1/files -> file_id
2. POST /api/v1/translate { file_id } -> 202 book_id
```

이 방향은 `FileUploadResponse.local_path` 노출 문제를 피하고, 번역 API를 JSON 기반 요청으로 단순화한다는 점에서 이전 설계보다 낫다. 다만 현재 서버 코드와 대조하면 신규 공용 업로드 API의 존재 여부, 파일 소유권 검증, 파일 크기 재검증이 추가로 필요하다.

### High - `POST /api/v1/files`가 현재 기존 엔드포인트가 아님

Design은 파일 업로드가 기존 `/api/v1/files` 엔드포인트를 사용한다고 설명한다. 하지만 현재 서버의 `app.core.files.router`는 `GET /files/{uuid}` 다운로드 라우터만 제공한다. 현재 존재하는 업로드 API는 게시판 전용 `POST /api/v1/boards/{board_code}/uploads`이다.

권장 보완:

- `POST /api/v1/files`를 SFR-106 범위의 신규 공용 업로드 API로 명시
- 또는 기존 게시판 업로드 API를 재사용할 것인지 명확히 결정
- 신규 공용 업로드 API를 만든다면 인증, MIME/크기 검증, response schema를 API 명세에 추가

### High - `file_id` 소유권 검증 누락

번역 요청이 `file_id`만 받는 구조에서는 파일 소유권 검증이 필수다. 현재 Design은 파일 존재와 MIME만 확인한다.

권장 보완:

- `file_entity.created_by == payload["sub"]` 검증 추가
- 실패 시 `403 FILE_ACCESS_FORBIDDEN` 또는 기존 파일 권한 오류 코드와 일관된 코드 사용
- 테스트 전략에 타인 file_id로 번역 요청 시 403 케이스 추가

### High - 10MB 제한 재검증 누락

Plan 요구사항에는 업로드 파일 최대 10MB 제한이 있다. 2단계 구조에서는 업로드 단계와 번역 요청 단계가 분리되므로, 번역 요청에서도 `File.file_size`를 기준으로 재검증해야 한다.

권장 보완:

- `file_entity.file_size > 10 * 1024 * 1024`이면 `400 IMAGE_SIZE_EXCEEDED`
- 업로드 API에서 이미 검증하더라도 translate service에서 방어적으로 재검증
- 테스트 전략에 10MB 초과 file_id 요청 케이스 추가

### Medium - 파일 없음 오류 코드가 기존 패턴과 다름

Design은 file_id에 해당하는 파일이 없을 때 `400 INVALID_FILE_ID`를 반환한다고 한다. 현재 파일 조회 계열은 파일 없음에 `404 FILE_NOT_FOUND`를 사용한다.

권장 보완:

- 기존 서버 패턴과 맞춰 `404 FILE_NOT_FOUND`로 정리
- 보안상 존재 여부를 숨기려는 의도가 있다면 `400 INVALID_FILE_ID` 유지 사유를 문서에 명시

### Low - 외부 의존성 설명 보정 권장

Design은 `google-genai`가 이미 설치되어 있고 `google-generativeai` deprecated로 교체한다고 한다. 현재 `pyproject.toml`에는 `google-genai`와 `google-generativeai`가 모두 존재한다.

권장 보완:

- 신규 구현은 `google-genai`를 사용한다고 명시
- `google-generativeai`는 기존 의존성으로 남아 있으나 신규 코드에서는 사용하지 않는다고 정리

## 추가 결론 3 - 2026-05-14

파일 업로드와 번역 요청을 분리한 방향은 적절하다. 구현 가능 상태로 만들려면 `POST /api/v1/files`를 신규 범위로 명확히 정의하고, translate 요청에서 `file_id` 소유권과 10MB 제한을 재검증해야 한다. 이 두 검증이 빠지면 타인 파일 사용 및 요구사항 우회 가능성이 남는다.

## 추가 확인 4 - 2026-05-14

수정본에서 Plan은 업로드 API를 `POST /api/v1/uploads`로 정리했지만, Design은 아직 `/api/v1/files` 흐름과 이전 검증 설명이 남아 있다.

남은 발견 사항:

### High - Plan과 Design의 업로드 API 경로 불일치

Plan은 `POST /api/v1/uploads`를 일반 파일 업로드 신규 구현으로 정의한다. Design은 아키텍처와 API 설명에서 여전히 `POST /api/v1/files`를 기존 엔드포인트로 사용한다고 설명한다.

권장 보완:

- Design의 2단계 흐름을 `POST /api/v1/uploads -> file_id`, `POST /api/v1/translate { file_id } -> book_id`로 수정
- `/api/v1/uploads`가 신규 구현 API임을 Design 파일 구조 또는 변경 항목에 추가
- 기존 `/files/{uuid}` 다운로드 라우터와 혼동되지 않도록 업로드 API와 파일 서빙 API를 분리해 설명

### High - Design에 신규 업로드 API 명세가 없음

Plan에서 `POST /api/v1/uploads`를 신규 구현 범위로 넣었으므로 Design에도 해당 API 명세가 필요하다.

권장 보완:

- `POST /api/v1/uploads`
  - 인증: USER 이상
  - Content-Type: `multipart/form-data`
  - Body: `file: UploadFile`
  - Response: `FileUploadResponse`
  - 400 `INVALID_IMAGE_TYPE`
  - 400 `IMAGE_SIZE_EXCEEDED`
  - 401 `UNAUTHORIZED`

### High - Design에 `file_id` 소유권 검증이 아직 없음

Plan은 `file_id`로 조회한 `File.created_by == payload["sub"]` 검증을 명시했다. Design의 service 흐름은 파일 존재와 MIME만 확인한다.

권장 보완:

- `file_entity.created_by != user_id`이면 `403 FILE_ACCESS_FORBIDDEN`
- `POST /api/v1/translate` 오류 응답 명세에 403 추가
- 테스트 전략에 타인 file_id 요청 케이스 추가

### High - Design에 10MB 재검증이 아직 없음

Plan은 `File.file_size` 기준 10MB 재검증을 명시했다. Design은 translate service 흐름에서 MIME만 확인하고 크기 검증이 빠져 있다.

권장 보완:

- `file_entity.file_size > 10 * 1024 * 1024`이면 `400 IMAGE_SIZE_EXCEEDED`
- `POST /api/v1/translate` 오류 응답 명세에 크기 초과 케이스 추가
- 테스트 전략에 10MB 초과 file_id 요청 케이스 추가

### Medium - 파일 없음 오류 코드 정책 재확인 필요

Design은 존재하지 않는 file_id에 대해 `400 INVALID_FILE_ID`를 유지한다. 기존 파일 조회 계열은 파일 없음에 `404 FILE_NOT_FOUND`를 사용한다.

권장 보완:

- 기존 서버 패턴과 맞춰 `404 FILE_NOT_FOUND`로 통일
- `400 INVALID_FILE_ID`를 유지한다면 보안 또는 API 정책상 이유를 명시

## 추가 결론 4 - 2026-05-14

Design은 아직 Plan의 최신 API 분리 방향을 완전히 따라오지 못했다. 업로드 경로를 `/api/v1/uploads`로 통일하고, 신규 업로드 API 명세, file 소유권 검증, 10MB 재검증을 추가해야 구현 가능한 설계가 된다.
