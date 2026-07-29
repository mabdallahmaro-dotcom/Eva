from app.config import settings


def test_settings_defaults() -> None:
    assert settings.ai_model == "gpt-4o-mini"
    assert settings.sqlite_path == "data/eva_ai.db"
