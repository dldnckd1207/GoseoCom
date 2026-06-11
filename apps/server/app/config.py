from pydantic import computed_field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.common.enums import AppEnv, FileStorage, OcrEngine, TranslatorEngine

# 운영 환경에서 사용을 금지하는 취약 시크릿 값
_WEAK_SECRETS = {"change-me", ""}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # 앱 공통
    # 기본값은 안전한 PRODUCTION. 로컬 개발은 `APP_ENV=development`를 명시한다.
    app_env: AppEnv = AppEnv.PRODUCTION
    app_secret_key: str = "change-me"
    app_cors_origins: str = "http://localhost:3000,http://localhost:3001"
    app_client_url: str = "http://localhost:3000"  # OAuth 로그인 완료 후 리다이렉트 URL
    app_admin_url: str = "http://localhost:3001/admin"  # 관리자 OAuth 로그인 완료 후 리다이렉트 URL

    # PostgreSQL
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "haedok"
    postgres_user: str = "haedok"
    postgres_password: str = ""

    @computed_field  # type: ignore[prop-decorator]
    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    # JWT
    jwt_secret_key: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60
    jwt_refresh_token_expire_days: int = 30

    # OAuth — Google
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/auth/google/callback"

    # OAuth — Kakao
    kakao_client_id: str = ""
    kakao_client_secret: str = ""
    kakao_redirect_uri: str = "http://localhost:8000/auth/kakao/callback"

    # OCR
    ocr_engine: OcrEngine = OcrEngine.GOOGLE_VISION
    google_vision_api_key: str = ""

    # 번역
    translator_engine: TranslatorEngine = TranslatorEngine.GEMINI
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-haiku-4-5-20251001"

    # 파일 저장
    file_storage: FileStorage = FileStorage.LOCAL
    file_local_path: str = "./storage/files"
    file_url_prefix: str = "/files"

    # 스케줄러
    scheduler_auto_reply_interval_seconds: int = 60
    scheduler_comment_filter_interval_seconds: int = 300
    scheduler_comment_filter_batch_size: int = 20

    # 관리자
    # 시드 부트스트랩 전용 — 최초 관리자 지정에만 사용한다(시드 마이그레이션이 읽음).
    # 로그인 시 이메일 기반 자동 ADMIN 승격은 보안상 제거되었다(점검보고서 #3).
    initial_admin_emails: str = ""

    # AI 에이전트
    ai_agent_user_id: str = "USR_00000000"

    # 번역 과금 제한
    translate_daily_limit: int = 10  # 사용자별 일일 최대 번역 건수 (0 = 무제한)

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.app_cors_origins.split(",") if o.strip()]

    @property
    def admin_emails(self) -> list[str]:
        """시드 부트스트랩용 초기 관리자 이메일 목록 (런타임 로그인에서는 미사용)."""
        return [e.strip() for e in self.initial_admin_emails.split(",") if e.strip()]

    @model_validator(mode="after")
    def _validate_secrets(self) -> "Settings":
        """운영 환경에서 기본/빈 시크릿 키 사용 시 기동을 실패시킨다."""
        if self.app_env == AppEnv.PRODUCTION and (
            self.jwt_secret_key in _WEAK_SECRETS or self.app_secret_key in _WEAK_SECRETS
        ):
            raise ValueError(
                "운영 환경(APP_ENV=production)에서 기본/빈 시크릿 키를 사용할 수 없습니다. "
                "JWT_SECRET_KEY와 APP_SECRET_KEY를 안전한 랜덤 값으로 설정하세요."
            )
        return self


settings = Settings()
