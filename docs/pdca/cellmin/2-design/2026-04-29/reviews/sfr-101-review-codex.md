# SFR-101 Design 리뷰 - Codex

| 항목 | 내용 |
|------|------|
| 리뷰 대상 | `docs/pdca/cellmin/2-design/2026-04-29/sfr-101.md` |
| 기준 문서 | `docs/sdd/srs_p1/SFR-101_BE_게시판CRUD.md` |
| 리뷰 일자 | 2026-04-30 |
| 리뷰어 | Codex |

## 총평

Design 문서는 SFR-101 최종 설계를 구현 단위로 잘 분해하고 있다. Router, Service, Repository, Schema, 파일 업로드/서빙, 테스트 전략까지 포함되어 있어 구현 방향은 충분히 잡혀 있다.

이전 리뷰에서 지적했던 JWT `name` 클레임 영향 범위, `FileMapRepository.upsert()`의 `file_group`, Pydantic list 기본값, files router 경로 표기는 모두 반영되었다.

## 발견 사항

현재 문서 기준으로 구현을 막는 누락이나 잘못된 설계는 보이지 않는다.

### 확인 완료 항목

- `app/auth/service.py`의 `login_or_register()`와 `refresh()` 양쪽 JWT 변경 영향 반영
- `tests/test_auth.py` 변경 대상 추가
- `create_access_token(user_id, user_level, user_name="", blocked=False)` 형태로 기존 호출 보호
- `FileMapRepository.upsert(..., file_group="attachment", sort_order=0)` 반영
- `PostCreateRequest.file_ids`, `CommentResponse.replies`에 `Field(default_factory=list)` 반영
- `APIRouter(prefix="/files")` 기준 route를 `/{uuid}`로 표기하고 최종 경로를 별도 명시

## 결론

Design 문서는 현재 상태로 구현 기준으로 사용할 수 있다. 추가 보완이 필요하다면 구현 중 실제 모델/라우터 코드와 맞춰 생기는 세부 차이를 반영하는 수준이면 충분하다.
