from unittest.mock import MagicMock

from app.models.stock import HistoricalPrice, StockData, StockInfo
from app.tools import FallbackProvider
from app.tools.cache import ProviderCache
from datetime import date


def _mock_data(ticker: str = "BBCA") -> StockData:
    return StockData(
        info=StockInfo(ticker=ticker, name="Test", sector="Tech"),
        history=[
            HistoricalPrice(date=date(2024, 1, 1), open=100, high=110, low=90, close=105, volume=1000),
        ],
    )


def test_health_summary_empty():
    p1 = MagicMock()
    p2 = MagicMock()
    cache = MagicMock()
    fb = FallbackProvider([p1, p2], cache)
    h = fb.health_summary()
    assert "ok=0" in h
    assert "fail=0" in h
    assert "rate_limited=0" in h


def test_health_summary_tracks_success():
    p1 = MagicMock()
    p1.fetch.return_value = _mock_data()
    p2 = MagicMock()
    cache = MagicMock()
    fb = FallbackProvider([p1, p2], cache)
    fb.fetch("BBCA")
    h = fb.health_summary()
    assert "ok=1" in h
    assert "fail=0" in h


def test_health_summary_tracks_failure():
    p1 = MagicMock()
    p1.fetch.return_value = None
    p2 = MagicMock()
    p2.fetch.return_value = None
    cache = MagicMock()
    cache.load.return_value = None
    fb = FallbackProvider([p1, p2], cache)
    fb.fetch("GAGAL")
    h = fb.health_summary()
    assert "ok=0" in h
    assert "fail=" in h


def test_health_summary_tracks_rate_limited():
    p1 = MagicMock()
    p1.fetch.side_effect = Exception("rate limit")
    p2 = MagicMock()
    p2.fetch.return_value = _mock_data("BBRI")
    cache = MagicMock()
    fb = FallbackProvider([p1, p2], cache)
    fb.fetch("BBCA")
    h = fb.health_summary()
    assert "rate_limited=1" in h
