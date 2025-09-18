from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App settings
    app_name: str = "Marketing Suite"
    debug: bool = False
    secret_key: str
    allowed_hosts: list[str] = ["localhost", "127.0.0.1"]
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8080"]

    # Database
    database_url: str

    # API Keys
    openai_api_key: str
    firecrawl_api_key: str
    google_places_api_key: str
    google_sheets_api_credentials: str | None = None

    # Redis for background tasks
    redis_url: str = "redis://localhost:6379/0"

    # Logging
    log_level: str = "INFO"

    # Rate limiting
    requests_per_minute: int = 60

    # Browser settings
    browser_headless: bool = True
    browser_timeout: int = 30000

    # Export settings
    max_export_rows: int = 10000
    export_formats: list[str] = ["csv", "excel", "json"]

    # Performance thresholds
    default_cpa_threshold: float = 50.0
    default_roas_threshold: float = 2.0
    alert_email: str | None = None

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
