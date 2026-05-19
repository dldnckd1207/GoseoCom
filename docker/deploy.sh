#!/bin/bash
set -e

cd "$(dirname "$0")"

echo "=== [1/3] 이미지 빌드 ==="
docker compose build

echo "=== [2/3] DB 마이그레이션 ==="
docker compose run --rm server uv run alembic upgrade head

echo "=== [3/3] 서비스 기동 ==="
docker compose up -d

echo ""
echo "=== 완료 ==="
docker compose ps
