from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Content Radar"
    environment: str = "development"
    timezone: str = "America/Sao_Paulo"

    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/content_radar"
    data_retention_days: int = 30

    @property
    def sqlalchemy_database_url(self):
        return self.database_url.replace(
            "postgresql://",
            "postgresql+psycopg://",
            1,
        )

    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
    gemini_model_name: str = Field(default="gemini-2.0-flash", alias="GEMINI_MODEL_NAME")
    telegram_token: str = Field(default="", alias="TELEGRAM_TOKEN")
    telegram_chat_id: str = Field(default="", alias="TELEGRAM_CHAT_ID")
    pipeline_api_key: str = Field(default="", alias="PIPELINE_API_KEY")

    enable_scheduler: bool = False
    scheduler_hour: int = 8
    scheduler_minute: int = 0
    collector_retry_attempts: int = 3
    collector_retry_delay_seconds: float = 1.5
    collector_timeout_seconds: float = 15.0
    reddit_user_agent: str = "Mozilla/5.0 ContentRadar/0.1"
    analysis_max_total_signals: int = 40
    analysis_max_news_signals: int = 20
    analysis_max_reddit_signals: int = 15
    analysis_max_trends_signals: int = 10
    analysis_max_content_length: int = 600

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
