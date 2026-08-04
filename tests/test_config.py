from app.config.settings import Settings


def test_settings_defaults() -> None:
    s = Settings(_env_file=None)
    assert s.ai_api_key == ""
    assert s.ai_model == ""
    assert s.ai_base_url == ""
    assert s.log_level == "INFO"


def test_settings_env_override(monkeypatch) -> None:
    monkeypatch.setenv("AI_API_KEY", "test-key")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    s = Settings()
    assert s.ai_api_key == "test-key"
    assert s.log_level == "DEBUG"
