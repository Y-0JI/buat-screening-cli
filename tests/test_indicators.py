from datetime import date
import pytest
from app.models.stock import HistoricalPrice
from app.indicators.engine import sma, ema, rsi, macd, atr, bollinger, adx, stochastic


def _make_prices(closes: list[float]) -> list[HistoricalPrice]:
    return [
        HistoricalPrice(
            date=date(2024, 1, (i % 30) + 1),
            open=c, high=c, low=c * 0.99, close=c, volume=1_000_000,
        )
        for i, c in enumerate(closes)
    ]


def _make_prices_full(highs: list[float], lows: list[float], closes: list[float]) -> list[HistoricalPrice]:
    return [
        HistoricalPrice(
            date=date(2024, 1, (i % 30) + 1),
            open=closes[i], high=highs[i], low=lows[i], close=closes[i], volume=1_000_000,
        )
        for i in range(len(closes))
    ]


class TestSMA:
    def test_sma_known(self):
        closes = [10, 20, 30, 40, 50]
        result = sma(_make_prices(closes), period=3)
        assert result[:2] == [None, None]
        assert result[2] == sum([10, 20, 30]) / 3
        assert result[3] == sum([20, 30, 40]) / 3
        assert result[4] == sum([30, 40, 50]) / 3

    def test_sma_period_1(self):
        result = sma(_make_prices([10, 20, 30]), period=1)
        assert result == [10.0, 20.0, 30.0]


class TestEMA:
    def test_ema_known(self):
        closes = [10, 20, 30, 40, 50]
        result = ema(_make_prices(closes), period=3)
        assert result[:2] == [None, None]
        assert result[2] == pytest.approx(sum([10, 20, 30]) / 3)
        multiplier = 2 / (3 + 1)
        expected_3 = (40 - result[2]) * multiplier + result[2]
        assert result[3] == pytest.approx(expected_3)
        expected_4 = (50 - result[3]) * multiplier + result[3]
        assert result[4] == pytest.approx(expected_4)


class TestRSI:
    def test_rsi_known(self):
        closes = [44.0, 44.34, 44.09, 43.61, 44.33, 44.83, 45.10, 45.42, 45.84, 46.08, 45.89, 46.03, 45.61, 46.28, 46.28, 46.00]
        result = rsi(_make_prices(closes), period=14)
        assert result[14] == pytest.approx(72.983871, abs=0.001)


class TestMACD:
    def test_macd_internally_consistent(self):
        closes = [float(i) for i in range(100, 150)]
        result = macd(_make_prices(closes))
        valid = [r for r in result if r is not None]
        assert len(valid) >= 1
        first = valid[0]
        assert "macd" in first and "signal" in first and "histogram" in first
        assert first["histogram"] == pytest.approx(first["macd"] - first["signal"])
        for r in valid:
            assert r["histogram"] == pytest.approx(r["macd"] - r["signal"])
        last = valid[-1]
        assert last["histogram"] == pytest.approx(last["macd"] - last["signal"])

    def test_macd_uptrend_positive(self):
        closes = [float(i) for i in range(100, 150)]
        result = macd(_make_prices(closes))
        valid = [r for r in result if r is not None]
        assert len(valid) > 0
        for r in valid:
            assert r["macd"] > 0

    def test_macd_short_data(self):
        result = macd(_make_prices([1, 2, 3]))
        assert all(r is None for r in result)


class TestATR:
    def test_atr_known_reference(self):
        highs = [110, 115, 112, 118, 120, 122]
        lows = [90, 95, 92, 98, 100, 102]
        closes = [105, 108, 106, 110, 115, 118]
        prices = _make_prices_full(highs, lows, closes)
        result = atr(prices, period=3)
        tr0 = max(highs[0] - lows[0], abs(highs[0] - closes[0]), abs(lows[0] - closes[0]))
        tr1 = max(highs[1] - lows[1], abs(highs[1] - closes[0]), abs(lows[1] - closes[0]))
        tr2 = max(highs[2] - lows[2], abs(highs[2] - closes[1]), abs(lows[2] - closes[1]))
        expected = (tr0 + tr1 + tr2) / 3
        assert result[3] == pytest.approx(expected)

    def test_atr_short_data(self):
        result = atr(_make_prices([1, 2]), period=14)
        assert all(r is None for r in result)


class TestBollinger:
    def test_bollinger_known(self):
        closes = [50.0] * 10
        result = bollinger(_make_prices(closes), period=5)
        valid = [r for r in result if r is not None]
        assert len(valid) >= 1
        last = valid[-1]
        assert last["middle"] == pytest.approx(50.0)
        assert last["upper"] == pytest.approx(50.0)
        assert last["lower"] == pytest.approx(50.0)

    def test_bollinger_bands_ordered(self):
        closes = [float(i) for i in range(50, 80)]
        result = bollinger(_make_prices(closes), period=5)
        valid = [r for r in result if r is not None]
        assert len(valid) >= 1
        assert all(v["upper"] > v["middle"] > v["lower"] for v in valid)


class TestADX:
    def test_adx_known_range(self):
        prices = [
            HistoricalPrice(
                date=date(2024, 1, (i % 28) + 1),
                open=100 + i, high=105 + i, low=95 + i, close=100 + i, volume=1_000_000,
            )
            for i in range(40)
        ]
        result = adx(prices, period=14)
        valid = [v for v in result if v is not None]
        assert len(valid) > 0
        for v in valid:
            assert 0 <= v <= 100

    def test_adx_short_data(self):
        result = adx(_make_prices([1, 2, 3]), period=14)
        assert all(r is None for r in result)


class TestStochastic:
    def test_stochastic_known_reference(self):
        highs = [127.09, 127.22, 126.83, 126.47, 126.76, 127.34, 127.29, 127.90,
                 128.40, 128.30, 128.05, 128.54, 128.60, 127.87, 127.56,
                 128.00, 128.20, 127.90]
        lows =  [125.90, 126.40, 126.16, 125.83, 126.00, 126.32, 126.12, 126.37,
                 127.00, 126.80, 126.58, 127.00, 127.29, 126.22, 126.16,
                 126.50, 126.80, 126.30]
        closes = [127.01, 127.02, 126.58, 126.22, 126.76, 127.24, 126.82, 127.62,
                  128.22, 127.70, 127.21, 128.06, 128.39, 126.86, 126.76,
                  127.50, 127.90, 127.30]
        prices = _make_prices_full(highs, lows, closes)
        result = stochastic(prices, period=14)
        stoch = result[13]
        assert stoch is not None
        assert "k" in stoch and stoch["d"] is None
        hh = max(highs[:14])
        ll = min(lows[:14])
        expected_k = (closes[13] - ll) / (hh - ll) * 100
        assert stoch["k"] == pytest.approx(expected_k, abs=0.01)
        stoch16 = result[16]
        assert stoch16 is not None and stoch16["d"] is not None
        k_vals = [result[14]["k"], result[15]["k"], stoch16["k"]]
        assert min(k_vals) <= stoch16["d"] <= max(k_vals)

    def test_stochastic_short_data(self):
        result = stochastic(_make_prices([1, 2]), period=14)
        assert all(r is None for r in result)
