FROM python:3.12-slim

# uv 설치
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app

# 시스템 의존성
RUN apt-get update && apt-get install -y \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 의존성 설치 (레이어 캐시 활용)
COPY apps/server/pyproject.toml apps/server/uv.lock* ./
RUN uv sync --frozen --no-dev

# 소스 복사
COPY apps/server/ .

# 파일 저장소 디렉토리
RUN mkdir -p /app/storage/files

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
