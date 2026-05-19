---
tags: [spec]
cssclasses:
  - my_style_width_100
status: active
created: 2026-04-15 00:00
updated: 2026-04-15 00:00
parent: "[[SRS_P1]]"
domain: "[[04_Domain]]"
requirement: "SFR-108"
---

# SFR-108 — 사용자 인증 (OAuth: Google + Kakao)

> [!note] 이 문서는 왜 작성하는가
> 하나의 기능을 어떻게 설계하고 구현할지 정리하는 문서.
> "결정 사항" 테이블에 왜 이 방식을 선택했는지 기록하는 것이 핵심이다.
> 이 문서가 나중에 포트폴리오와 회고의 기반이 된다.

---

## 배경

모든 쓰기 작업(게시글/댓글 작성, 번역기 사용, 라이브러리 접근)은 로그인이 필요하다.
LOCAL 로그인 없이 OAuth 전용으로 운영하며, 개인정보 최소 수집 원칙을 따른다.
JWT를 httpOnly 쿠키로 전달해 XSS 공격을 방어하고, Refresh Token Rotation으로 탈취를 감지한다.

---

## 기능 설명

Google / Kakao OAuth 2.0 로그인을 지원한다.
최초 로그인 시 유저를 자동 생성(UPSERT)하고, JWT Access/Refresh Token을 httpOnly 쿠키로 발급한다.
Refresh Token은 DB에 저장하여 강제 로그아웃 및 탈취 감지가 가능하다.

---

## 핵심 흐름

### OAuth 로그인 흐름

```
1. 클라이언트 → GET /auth/google (또는 /auth/kakao)
2. 서버 → OAuth Provider로 리다이렉트 (authorization_url)
3. 사용자 → Provider에서 로그인/동의
4. Provider → GET /auth/google/callback?code=xxx
5. 서버 → code로 access_token 교환
6. 서버 → Provider에서 사용자 정보 조회 (email, name, profile_image_url)
7. 서버 → com_tn_user UPSERT + com_tn_user_oauth UPSERT
8. 서버 → Access Token + Refresh Token 발급
9. 서버 → httpOnly 쿠키 설정 후 클라이언트로 리다이렉트
10. com_th_login_log INSERT (성공/실패 모두)
```

### Token 갱신 흐름

```
1. 클라이언트 → POST /auth/refresh (쿠키에 refresh_token 자동 포함)
2. 서버 → com_tn_user_token에서 token_hash 조회
3. is_revoked=true면 → 전체 세션 무효화 후 401
4. 유효하면 → 새 Access Token + 새 Refresh Token 발급
5. 이전 Refresh Token → is_revoked=true
6. 새 토큰 → httpOnly 쿠키 설정
```

### 로그아웃 흐름

```
1. 클라이언트 → POST /auth/logout
2. 서버 → com_tn_user_token에서 해당 token is_revoked=true
3. 서버 → 쿠키 삭제 (Max-Age=0)
```

---

## 설계

### 구조

- **영향 받는 레이어**: Router → Service → Repository
- **신규 생성**:
  - `app/auth/router.py`
  - `app/auth/service.py`
  - `app/auth/repository.py`
  - `app/auth/schemas.py`
  - `app/auth/oauth/google.py`
  - `app/auth/oauth/kakao.py`
  - `app/core/common/decorators/require_level.py`
- **변경 대상**: `app/main.py` (auth router 등록)
- **의존성**: `python-jose`, `httpx`, `passlib`(bcrypt for token hash)

### 데이터

#### com_tn_user

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | VARCHAR(20) | PK, `USR_00000001` |
| email | VARCHAR(255) | UNIQUE |
| name | VARCHAR(100) | |
| profile_image_url | VARCHAR(500) | |
| user_level | INT | 0/10/70/100 |
| use_yn | BOOLEAN | 기본 true |
| del_yn | BOOLEAN | 기본 false |

#### com_tn_user_oauth

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | VARCHAR(20) | PK, `OAUTH_00000001` |
| user_id | VARCHAR(20) | FK → com_tn_user |
| provider | VARCHAR(20) | `GOOGLE` \| `KAKAO` |
| provider_user_id | VARCHAR(255) | |
| provider_email | VARCHAR(255) | |

#### com_tn_user_token

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | VARCHAR(20) | PK, `UTKN_00000001` |
| user_id | VARCHAR(20) | FK → com_tn_user |
| token_hash | VARCHAR(255) | bcrypt 해시 |
| expires_at | TIMESTAMPTZ | 30일 |
| is_revoked | BOOLEAN | 기본 false |

#### com_th_login_log

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | BIGSERIAL | PK |
| user_id | VARCHAR(20) | nullable (실패 시 null) |
| provider | VARCHAR(20) | `GOOGLE` \| `KAKAO` |
| login_result | VARCHAR(20) | `SUCCESS` \| `FAIL` |
| ip_address | VARCHAR(50) | |
| created_at | TIMESTAMPTZ | |

### 인터페이스

**API**

| Method | Path | 설명 | 인증 |
|--------|------|------|------|
| GET | `/auth/google` | Google OAuth 시작 | 불필요 |
| GET | `/auth/google/callback` | Google 콜백 처리 | 불필요 |
| GET | `/auth/kakao` | Kakao OAuth 시작 | 불필요 |
| GET | `/auth/kakao/callback` | Kakao 콜백 처리 | 불필요 |
| POST | `/auth/refresh` | Access Token 갱신 | Refresh Token (쿠키) |
| POST | `/auth/logout` | 로그아웃 | Access Token (쿠키) |
| GET | `/api/v1/users/me` | 내 정보 조회 | Access Token (쿠키) |

**쿠키**

| 쿠키명 | 내용 | 만료 |
|--------|------|------|
| `access_token` | JWT | 1시간 |
| `refresh_token` | JWT | 30일 |

- `httpOnly=true`, `SameSite=Lax`, `Secure=true`(운영), `Path=/`

**httpOnly 쿠키 보안 특성:**

| 공격 유형 | 방어 여부 | 적용 설정 |
|----------|---------|---------|
| XSS (JavaScript 탈취) | ✅ 방어 | `httpOnly=true` — JS에서 `document.cookie` 접근 불가 |
| CSRF (위조 요청) | ✅ 방어 | `SameSite=Lax` — 외부 사이트에서 자동 전송 차단 |
| 네트워크 스니핑 | ✅ 방어 | `Secure=true` — HTTPS에서만 전송 |

**Access Token 검증 방식 (Stateless):**
- 모든 API 요청: JWT 서명 검증 + 만료 확인만 수행 → **DB 조회 없음**
- httpOnly 쿠키는 JWT의 저장/전송 수단일 뿐, 서버 세션을 유지하지 않음
- 강제 로그아웃/탈취 차단의 즉각 효과: Refresh Token은 즉시, Access Token은 만료(1시간) 후

**에러 응답**

| 상황 | HTTP | code |
|------|------|------|
| 토큰 없음/만료 | 401 | `UNAUTHORIZED` |
| 권한 부족 | 403 | `FORBIDDEN` |
| 탈취 감지 (revoked token 재사용) | 401 | `TOKEN_REUSE_DETECTED` |

---

## 결정 사항

| 주제 | 선택 | 이유 (트레이드오프 포함) | 검토한 대안 |
|------|------|--------------------------|-------------|
| 인증 방식 | JWT + httpOnly 쿠키 | XSS 방어(`httpOnly`) + CSRF 방어(`SameSite=Lax`) + Stateless 유지 | Session(Stateful, Redis 필요), Bearer 헤더(XSS 취약 — localStorage 탈취 가능) |
| Access Token 검증 | Stateless (서명/만료만 확인) | DB 조회 없어 성능 우수. 만료(1시간)까지 즉각 차단 불가는 트레이드오프 | 매 요청마다 DB 조회 (즉각 차단 가능하나 Stateless 포기) |
| Refresh Token 저장 | DB (com_tn_user_token) | 강제 로그아웃, 탈취 감지 가능 | 저장 안 함(탈취 대응 불가) |
| Token Rotation | 사용 시 새 토큰 발급 + 이전 무효화 | revoked 토큰 재사용 감지 → 전체 세션 무효화로 탈취 차단 | 미적용(보안 취약) |
| LOCAL 로그인 | 미지원 | 개인정보 최소 수집, 구현 복잡도 감소 | ID/PW 지원(비밀번호 관리 부담) |
| user UPSERT | OAuth 콜백에서 자동 생성 | 별도 회원가입 불필요 | 회원가입 분리(UX 복잡) |
| 개발용 토큰 | `POST /auth/dev/token` (dev 환경만) | OAuth 없이 Swagger/Postman 테스트 가능 | 없음(매번 브라우저 OAuth 필요), 개발용 엔드포인트(운영 노출 위험 — APP_ENV 체크 필수) |
| Enum 위치 | `app/core/common/enums.py` | 다른 도메인이 config 의존 없이 import 가능, 단일 책임 원칙 | config.py 내 정의(도메인 간 결합도 증가) |

---

## 의존 기능

- 선행: SFR-100 (기반 구축) ✅
- 후행: 모든 SFR (인증이 기반)

---

## 미결/리스크

- [x] Google OAuth Client ID/Secret 발급 (.env 설정 완료)
- [x] Kakao OAuth Client ID/Secret 발급 (.env 설정 완료)
- [ ] 콜백 URL을 운영 도메인으로 변경 시 Provider 설정 업데이트 필요 (Phase 1은 localhost)
- [ ] Access Token 만료 시 클라이언트 자동 갱신 처리 (Remix loader에서 처리 방식 확정 필요)
- [ ] 동일 이메일로 Google + Kakao 둘 다 연결 시 처리 (같은 user_id에 두 oauth 연결)

**확정된 처리 방식:**
- **탈퇴 유저 재로그인**: OAuth 콜백에서 `del_yn=true` 확인 → `left_at + 90일` 이내면 로그인 거부. 90일 이후엔 이메일 익명화로 신규 가입 처리됨
- **AI 에이전트 시드**: Alembic 데이터 마이그레이션으로 `USR_00000000` ("해독이") 레코드 INSERT. 마이그레이션이 앱 기동 전 실행되므로 앱 startup 체크 불필요
- **OAuth state CSRF 방어**: authlib이 내부적으로 state 생성/검증 처리. 서명된 쿠키에 state 저장
- **Refresh Token 해시**: bcrypt → HMAC-SHA256 (성능 개선, `app/core/security.py`에서 관리)
- **Rotation 레이스 컨디션**: 30초 grace period 적용 (다중 탭/기기 동시 갱신 허용)
- **JWT 라이브러리**: python-jose → PyJWT (유지보수 활성화)
- **authlib**: OAuth 클라이언트용 (state, PKCE 자동 처리)
- **dev 라우터**: 라우터 등록 자체를 dev 환경 조건 분기
- **만료 레코드 정리**: 만료 + 7일 후 배치 삭제 (탈취 감지 보존 기간)
- **기기 정보**: `com_tn_user_token`에 `user_agent`, `ip_address` 컬럼 추가

---

## 테스트 기준

**정상:**
- Google 로그인 성공 → httpOnly 쿠키 발급, DB에 user/oauth/token 레코드 생성
- Kakao 로그인 성공 → 동일
- 동일 이메일로 재로그인 → UPSERT (신규 생성 아님)
- Google + Kakao 같은 이메일 연결 → 동일 `user_id`에 두 oauth 레코드 연결
- Refresh Token으로 갱신 → 새 토큰 발급, 이전 토큰 revoked
- 여러 기기 동시 로그인 → 각각 독립 토큰 발급, 한 기기 로그아웃이 다른 기기에 영향 없음
- 로그아웃 → 쿠키 삭제, 해당 기기 token revoked
- 비로그인으로 `/api/v1/users/me` → 401
- login_log → 성공/실패 모두 기록 확인

**예외:**
- 만료된 Access Token → 401 (클라이언트가 refresh 시도)
- Refresh Token 30일 만료 → 401
- 이미 revoked된 Refresh Token 재사용 → 401 `TOKEN_REUSE_DETECTED` + 전체 세션 무효화
- OAuth Provider 오류 → login_log에 FAIL 기록, 에러 페이지
- 탈퇴 후 90일 이내 재로그인 시도 → 거부
- `USR_00000000` AI 에이전트 계정으로 로그인 시도 → 차단
- `/auth/dev/token`을 production 환경에서 호출 → 404

---

## 참고

- [SRS_P1 §3.2 인증/권한](../specs/srs/SRS_P1.md)
- [05_ERD §3.1 User 도메인](../specs/05_ERD.md)
- [03_Architecture §4 인증 흐름](../specs/03_Architecture.md)
