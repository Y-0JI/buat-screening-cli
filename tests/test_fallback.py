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


def test_fallback_primary_success():
    p1 = MagicMock()
    p1.fetch.return_value = _mock_data()
    p2 = MagicMock()
    cache = MagicMock()
    fb = FallbackProvider([p1, p2], cache)
    result = fb.fetch("BBCA")
    assert result is not None
    p1.fetch.assert_called_once()
    p2.fetch.assert_not_called()
    cache.save.assert_called_once()


def test_fallback_to_secondary():
    p1 = MagicMock()
    p1.fetch.return_value = None
    p2 = MagicMock()
    p2.fetch.return_value = _mock_data("BBRI")
    cache = MagicMock()
    fb = FallbackProvider([p1, p2], cache)
    result = fb.fetch("BBRI")
    assert result is not None
    assert result.info.ticker == "BBRI"
    p1.fetch.assert_called_once()
    p2.fetch.assert_called_once()
    cache.save.assert_called_once()


def test_fallback_all_fail_cached():
    p1 = MagicMock()
    p1.fetch.return_value = None
    p2 = MagicMock()
    p2.fetch.return_value = None
    cache = MagicMock()
    cache.load.return_value = _mock_data("CACHED")
    fb = FallbackProvider([p1, p2], cache)
    result = fb.fetch("CACHED")
    assert result is not None
    assert result.info.ticker == "CACHED"
    cache.load.assert_called_once()


def test_fallback_all_fail_no_cache():
    p1 = MagicMock()
    p1.fetch.return_value = None
    p2 = MagicMock()
    p2.fetch.return_value = None
    cache = MagicMock()
    cache.load.return_value = None
    fb = FallbackProvider([p1, p2], cache)
    result = fb.fetch("GAGAL")
    assert result is None
