import os
import tempfile
from datetime import date, timedelta

from app.tools.cache import ProviderCache
from app.models.stock import HistoricalPrice, StockData, StockInfo


def _mock_data() -> StockData:
    return StockData(
        info=StockInfo(ticker="TEST", name="Test Co", sector="Tech", market_cap=1_000_000, currency="IDR"),
        history=[
            HistoricalPrice(date=date(2024, 1, 1), open=100, high=110, low=90, close=105, volume=1000),
            HistoricalPrice(date=date(2024, 1, 2), open=106, high=115, low=95, close=110, volume=1200),
        ],
    )


def _empty_cache_dir():
    d = tempfile.mkdtemp()
    return d


def test_cache_save_load():
    d = _empty_cache_dir()
    c = ProviderCache(cache_dir=d, ttl_hours=24)
    data = _mock_data()
    c.save("BBCA", "6mo", True, data)
    loaded = c.load("BBCA", "6mo", True)
    assert loaded is not None
    assert loaded.info.ticker == "TEST"
    assert loaded.info.name == "Test Co"
    assert len(loaded.history) == 2


def test_cache_miss():
    d = _empty_cache_dir()
    c = ProviderCache(cache_dir=d, ttl_hours=24)
    loaded = c.load("NONEXISTENT", "6mo", True)
    assert loaded is None


def test_cache_expired():
    d = _empty_cache_dir()
    c = ProviderCache(cache_dir=d, ttl_hours=0)  # TTL 0 = langsung expired
    data = _mock_data()
    c.save("BBCA", "6mo", True, data)
    loaded = c.load("BBCA", "6mo", True)
    assert loaded is None


def test_cache_stale():
    d = _empty_cache_dir()
    c = ProviderCache(cache_dir=d, ttl_hours=0)
    c.save("BBCA", "6mo", True, _mock_data())
    loaded = c.load("BBCA", "6mo", True, allow_stale=True)
    assert loaded is not None


def test_fresh_cache_skips_provider():
    from unittest.mock import Mock
    from app.tools import FallbackProvider
    d = _empty_cache_dir()
    fp = FallbackProvider(providers=[], cache=ProviderCache(cache_dir=d, ttl_hours=24))
    fp.cache.save("BBCA", "6mo", True, _mock_data())
    provider = Mock()
    provider.fetch.return_value = None
    fp.providers = [provider]
    got = fp.fetch("BBCA", "6mo", True)
    assert got is not None, "cache segar harus dipakai tanpa memanggil provider"
    provider.fetch.assert_not_called()


def test_expired_cache_calls_provider():
    from unittest.mock import Mock
    from app.tools import FallbackProvider
    d = _empty_cache_dir()
    provider = Mock()
    provider.fetch.return_value = None
    fp = FallbackProvider(providers=[provider], cache=ProviderCache(cache_dir=d, ttl_hours=0))
    fp.cache.save("BBCA", "6mo", True, _mock_data())
    fp.fetch("BBCA", "6mo", True)
    provider.fetch.assert_called_once()
