from datetime import date
import pytest
from app.models.stock import HistoricalPrice
from app.indicators.engine import sma, ema, rsi, macd, atr, bollinger, stochastic


def _make_prices(closes: list[float], highs: list[float] | None = None, lows: list[float] | None = None) -> list[HistoricalPrice]:
    h = highs or closes
    l = lows or [c * 0.99 for c in closes]
    return [
        HistoricalPrice(
            date=date(2024, 1, (i % 30) + 1),
            open=c,
            high=h[i],
            low=l[i],
            close=c,
            volume=1_000_000,
        )
        for i, c in enumerate(closes)
    ]


class TestSMA:
    def test_sma_basic(self):
        prices = _make_prices([10.0, 20.0, 30.0, 40.0, 50.0])
        result = sma(prices, period=3)
        assert result[:2] == [None, None]
        assert result[2] == pytest.approx(20.0)
        assert result[3] == pytest.approx(30.0)
        assert result[4] == pytest.approx(40.0)

    def test_sma_period_1(self):
        prices = _make_prices([10.0, 20.0])
        result = sma(prices, period=1)
        assert result[0] == 10.0
        assert result[1] == 20.0


class TestEMA:
    def test_ema_basic(self):
        prices = _make_prices([10.0, 20.0, 30.0, 40.0, 50.0])
        result = ema(prices, period=3)
        assert result[:2] == [None, None]
        assert result[2] == pytest.approx(20.0)
        assert result[3] == pytest.approx(30.0)
        assert result[4] == pytest.approx(40.0)


class TestRSI:
    def test_rsi_period(self):
        prices = _make_prices([44, 44.34, 44.09, 43.61, 44.33, 44.83, 45.10, 45.42, 45.84, 46.08, 45.89, 46.03, 45.61, 46.28, 46.28, 46.00, 46.03, 46.41, 46.22, 45.64])
        result = rsi(prices, period=14)
        assert result[14] is not None
        assert 50 < result[14] < 80


class TestMACD:
    def test_macd_returns_dicts(self):
        prices = _make_prices([float(i) for i in range(1, 60)])
        result = macd(prices)
        valid = [r for r in result if r is not None]
        assert len(valid) > 0
        assert "macd" in valid[0]
        assert "signal" in valid[0]
        assert "histogram" in valid[0]


class TestATR:
    def test_atr_positive(self):
        prices = _make_prices([10.0] * 20)
        result = atr(prices, period=14)
        assert result[14] is not None
        assert result[14] > 0


class TestBollinger:
    def test_bollinger_structure(self):
        prices = _make_prices([float(i) for i in range(1, 30)])
        result = bollinger(prices, period=5)
        valid = [r for r in result if r is not None]
        assert len(valid) > 0
        assert valid[0]["upper"] > valid[0]["middle"]
        assert valid[0]["lower"] < valid[0]["middle"]


class TestStochastic:
    def test_stochastic_range(self):
        prices = _make_prices([float(i) for i in range(1, 30)])
        result = stochastic(prices, period=5)
        valid = [r for r in result if r is not None]
        assert len(valid) > 0
        assert 0 <= valid[0]["k"] <= 100
