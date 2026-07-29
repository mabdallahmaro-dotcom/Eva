from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Telegram
    bot_token: str | None = None

    # AI
    ai_provider: str = "gemini"
    ai_api_key: str | None = None
    ai_base_url: str = "https://api.openai.com/v1"
    ai_model: str = "gemini-2.5-flash"

    # Database
    sqlite_path: str = "data/eva_ai.db"

    # Logging
    log_level: str = "INFO"

    # Web Search
    web_search_enabled: bool = False
    web_search_api_key: str | None = None

    # Timezone
    timezone: str = "UTC"


settings = Settings()
