-- =============================================================================
-- Haedok AI — PostgreSQL 초기화 스크립트
-- Docker Compose 로 PostgreSQL 컨테이너를 처음 띄울 때만 실행됩니다.
-- 테이블 생성은 Alembic 마이그레이션으로 관리합니다.
-- =============================================================================

-- DB / 유저는 docker-compose.yml 환경변수(POSTGRES_DB, POSTGRES_USER)로 생성되므로
-- 여기서는 확장 모듈 설치와 기본 설정만 처리합니다.

-- uuid_generate_v4() 사용을 위한 확장 (SQLAlchemy에서 gen_random_uuid() 사용 시 불필요)
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 전문검색 (Phase 2 이상 활용 예정)
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
