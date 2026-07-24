import pytest
from app.tools.base import StockProvider
from app.tools.registry import ProviderRegistry


class _DummyProvider(StockProvider):
    def fetch(self, ticker, period="6mo"):
        return None
    def get_price(self, ticker):
        return None


def test_register_and_get():
    reg = ProviderRegistry()
    p = _DummyProvider()
    reg.register("test", p, default=True)
    assert reg.get() is p
    assert reg.get("test") is p


def test_default_fallback_to_first():
    reg = ProviderRegistry()
    p1 = _DummyProvider()
    p2 = _DummyProvider()
    reg.register("a", p1)
    reg.register("b", p2)
    assert reg.get() is p1


def test_list():
    reg = ProviderRegistry()
    p = _DummyProvider()
    reg.register("x", p)
    assert reg.list() == {"x": p}


def test_set_default():
    reg = ProviderRegistry()
    p1 = _DummyProvider()
    p2 = _DummyProvider()
    reg.register("a", p1)
    reg.register("b", p2)
    assert reg.get() is p1
    reg.set_default("b")
    assert reg.get() is p2


def test_set_default_invalid_raises():
    reg = ProviderRegistry()
    reg.register("a", _DummyProvider())
    with pytest.raises(ValueError):
        reg.set_default("nonexistent")


def test_get_empty_raises():
    reg = ProviderRegistry()
    with pytest.raises(ValueError):
        reg.get()
