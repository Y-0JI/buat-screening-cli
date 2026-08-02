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
    cache.load.return_value = None
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
    cache.load.return_value = None
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
    p1.fetch.assert_not_called()
    p2.fetch.assert_not_called()


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


def test_fallback_rejects_invalid_symbol():
    p1 = MagicMock()
    p2 = MagicMock()
    cache = MagicMock()
    fb = FallbackProvider([p1, p2], cache)
    result = fb.fetch("")
    assert result is None
    p1.fetch.assert_not_called()
    p2.fetch.assert_not_called()
    cache.save.assert_not_called()


def test_fetch_financials_retries_on_rate_limit():
    from unittest.mock import Mock, patch
    from app.tools.yahoo_finance import YahooFinanceProvider
    calls = {"n": 0}

    class Flaky:
        @property
        def financials(self):
            calls["n"] += 1
            if calls["n"] == 1:
                raise Exception("Too many requests")
            return Mock(empty=False, to_json=lambda **kw: '{"2025-12-31": {"Total Revenue": 1}}')
        @property
        def balance_sheet(self):
            return Mock(empty=False, to_json=lambda **kw: "{}")
        @property
        def cashflow(self):
            return Mock(empty=False, to_json=lambda **kw: "{}")
        @property
        def dividends(self):
            return Mock(empty=False, to_json=lambda **kw: "{}")

    with patch("app.tools.yahoo_finance.yf.Ticker", return_value=Flaky()):
        with patch("app.tools.yahoo_finance.time.sleep", return_value=None):
            p = YahooFinanceProvider()
            out = p.fetch_financials("BBCA")
    assert calls["n"] == 2, "1x rate-limit + 1x retry sukses"
    assert "financials" in out, "rate-limit harus di-retry, bukan langsung gagal"


def test_fetch_financials_merges_across_providers():
    p1 = MagicMock()
    p1.fetch_financials.return_value = {"financials": {"2026-03-31": {"Total Revenue": 8004.91}}}
    p2 = MagicMock()
    p2.fetch_financials.return_value = {"derived": {"2026-03-31": {"Diluted EPS": 286.52, "Book Value": 3136.99}}}
    cache = MagicMock()
    cache.load_json.return_value = None
    fb = FallbackProvider([p1, p2], cache)
    out = fb.fetch_financials("BBCA")
    assert out["financials"]["2026-03-31"]["Total Revenue"] == 8004.91
    assert out["derived"]["2026-03-31"]["Diluted EPS"] == 286.52
    assert out["derived"]["2026-03-31"]["Book Value"] == 3136.99
    p1.fetch_financials.assert_called_once()
    p2.fetch_financials.assert_called_once()
    cache.save_json.assert_called_once()


def test_fetch_financials_no_short_circuit_on_first_truthy():
    p1 = MagicMock()
    p1.fetch_financials.return_value = {"financials": {"2026-03-31": {"Total Revenue": 8004.91}}}
    p2 = MagicMock()
    p2.fetch_financials.return_value = {"derived": {"2026-03-31": {"Diluted EPS": 286.52}}}
    cache = MagicMock()
    cache.load_json.return_value = None
    fb = FallbackProvider([p1, p2], cache)
    out = fb.fetch_financials("BBCA")
    assert p2.fetch_financials.call_count == 1, "provider kedua tetap dipanggil walau yang pertama non-empty"
    assert "derived" in out
