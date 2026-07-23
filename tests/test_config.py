from app.config.settings import Settings


def test_settings_defaults() -> None:
    s = Settings()
    assert s.openrouter_api_key == ""
    assert s.openrouter_model == "openai/gpt-4o-mini"
    assert s.log_level == "INFO"


def test_settings_env_override(monkeypatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    s = Settings()
    assert s.openrouter_api_key == "test-key"
    assert s.log_level == "DEBUG"
