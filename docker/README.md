# Docker 배포

## 디렉토리 구조

```
docker/
├── docker-compose.yml      # server + client 서비스 정의
├── deploy.sh               # 빌드 → 마이그레이션 → 기동 일괄 스크립트
├── server/
│   └── Dockerfile          # FastAPI (Python 3.12 + uv)
├── client/
│   └── Dockerfile          # Remix SSR (Node.js 20)
└── volumes/
    └── nginx/
        └── nginx.conf      # 외부 nginx 참조용 설정 예시
```

> **PostgreSQL**은 별도 운영합니다. docker-compose에 포함되지 않습니다.

---

## 사전 준비

### 1. Docker 네트워크 생성

서비스는 외부 네트워크 `mynet`을 사용합니다. 없으면 먼저 생성하세요.

```bash
# 네트워크 존재 확인
docker network ls | grep mynet

# 없으면 생성
docker network create \
  --driver bridge \
  --subnet 172.20.0.0/16 \
  --gateway 172.20.0.1 \
  mynet
```

### 2. 버전 설정

```bash
cp docker/.env.example docker/.env
```

`.env` 설정 항목:

| 항목 | 기본값 | 설명 |
|------|--------|------|
| `APP_VERSION` | `0.1.0` | 이미지 태그 (`haedok-server:0.1.0`) |
| `SERVER_PORT` | `8000` | FastAPI 외부 노출 포트 |
| `CLIENT_PORT` | `3000` | Remix SSR 외부 노출 포트 |
| `PUBLIC_API_URL` | `http://localhost:8000` | 브라우저에서 접근하는 BE 공개 URL (OAuth 리다이렉트 등) |

### 3. 환경 변수

```bash
# 서버
cp apps/server/.env.example apps/server/.env
# 필수 항목 채우기:
# - POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD
# - JWT_SECRET_KEY, APP_SECRET_KEY
# - GOOGLE_CLIENT_ID/SECRET, KAKAO_CLIENT_ID/SECRET
# - GOOGLE_VISION_API_KEY, GEMINI_API_KEY

# 클라이언트
cp apps/client/.env.example apps/client/.env
# VITE_API_BASE_URL은 docker-compose에서 빌드 시 주입됩니다 (수동 설정 불필요)
```

### 2. PostgreSQL 계정 및 데이터베이스 생성

서비스 전용 계정과 DB를 먼저 생성합니다. (PostgreSQL 슈퍼유저로 실행)

```sql
-- 1. 사용자 생성
CREATE USER haedok WITH PASSWORD 'your_password';

-- 2. 데이터베이스 생성
CREATE DATABASE haedok OWNER haedok;
```

생성한 DB에 접속 후 권한 부여:

```sql
\c haedok

GRANT ALL ON SCHEMA public TO haedok;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO haedok;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO haedok;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO haedok;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO haedok;
```

또는 psql 명령으로 한 번에 실행:

```bash
psql -U postgres -h localhost -p 5432 -c "
CREATE USER haedok WITH PASSWORD 'your_password';
CREATE DATABASE haedok OWNER haedok;
" && psql -U postgres -h localhost -p 5432 -d haedok -c "
GRANT ALL ON SCHEMA public TO haedok;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO haedok;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO haedok;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO haedok;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO haedok;
"
```

> **Docker 컨테이너 → 호스트 DB 접근 시:** `POSTGRES_HOST`를 `localhost` 대신 `host.docker.internal` (Mac/Windows) 또는 실제 IP로 설정하세요.

### 3. PostgreSQL 연결 확인

```bash
# 서버 .env의 POSTGRES_HOST가 Docker 컨테이너에서 접근 가능한지 확인
psql -U haedok -h localhost -p 5432 -d haedok -c "SELECT 1;"
```

---

## 배포

### 전체 배포 (빌드 + 마이그레이션 + 기동)

```bash
cd docker
./deploy.sh
```

내부 순서:
1. 이미지 빌드 (`docker compose build`)
2. DB 마이그레이션 (`alembic upgrade head`)
3. 서비스 기동 (`docker compose up -d`)

### 단계별 수동 실행

```bash
cd docker

# 빌드
docker compose build

# 마이그레이션
docker compose run --rm server uv run alembic upgrade head

# 기동
docker compose up -d

# 상태 확인
docker compose ps
```

---

## 운영

```bash
# 로그 확인
docker compose logs -f server
docker compose logs -f client

# 재시작
docker compose restart server

# 중지
docker compose down

# 이미지 재빌드 후 재배포
docker compose build server
docker compose up -d server
```

---

## 포트

| 서비스 | 내부 포트 | 호스트 노출 |
|--------|-----------|------------|
| server (FastAPI) | 8000 | 8000 |
| client (Remix SSR) | 3000 | 3000 |

외부 nginx 설정 예시 (`docker/volumes/nginx/nginx.conf` 참조):
- `/api/*`, `/auth/*`, `/files/*`, `/admin/api/*` → `server:8000`
- `/*` → `client:3000`

---

## 파일 업로드 볼륨

게시글/번역 첨부파일은 `server_files` Docker 볼륨에 저장됩니다.

```bash
# 볼륨 확인
docker volume ls | grep server_files

# 볼륨 위치 (백업 시 참조)
docker volume inspect docker_server_files
```
