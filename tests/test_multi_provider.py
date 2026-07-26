import importlib


def test_get_provider_by_name():
    from app.tools import get_provider
    yahoo = get_provider("yahoo")
    assert yahoo is not None
    assert type(yahoo).__name__ == "YahooFinanceProvider"
    idx = get_provider("idx")
    assert idx is not None
    assert type(idx).__name__ == "IDXProvider"


def test_default_provider_from_config_yahoo(monkeypatch):
    monkeypatch.setenv("DATA_PROVIDER", "yahoo")
    import app.tools
    importlib.reload(app.tools)
    from app.tools import get_provider
    provider = get_provider()
    assert type(provider).__name__ == "YahooFinanceProvider"


def test_default_provider_from_config_idx(monkeypatch):
    monkeypatch.setenv("DATA_PROVIDER", "idx")
    import app.config.settings
    import app.tools
    importlib.reload(app.config.settings)
    importlib.reload(app.tools)
    from app.tools import get_provider
    provider = get_provider()
    assert type(provider).__name__ == "IDXProvider"


def test_default_provider_fallback_on_invalid_config(monkeypatch):
    monkeypatch.setenv("DATA_PROVIDER", "nonexistent")
    import app.config.settings
    import app.tools
    importlib.reload(app.config.settings)
    importlib.reload(app.tools)
    from app.tools import get_provider
    provider = get_provider()
    assert type(provider).__name__ == "YahooFinanceProvider"
