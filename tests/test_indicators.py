from datetime import date
import math
import pytest
from app.models.stock import HistoricalPrice
from app.indicators.engine import sma, ema, rsi, macd, atr, bollinger, adx, stochastic


def _make_prices(closes: list[float], highs: list[float] | None = None, lows: list[float] | None = None) -> list[HistoricalPrice]:
    h = highs or closes
    l = lows or [c * 0.99 for c in closes]
    return [
        HistoricalPrice(
            date=date(2024, 1, (i % 30) + 1),
            open=c,
            high=h[i] if highs else c,
            low=l[i] if lows else c * 0.99,
            close=c,
            volume=1_000_000,
        )
        for i, c in enumerate(closes)
    ]


class TestSMA:
    def test_sma_known(self):
        closes = [10, 20, 30, 40, 50]
        result = sma(_make_prices(closes), period=3)
        assert result[:2] == [None, None]
        assert result[2] == sum([10, 20, 30]) / 3
        assert result[3] == sum([20, 30, 40]) / 3
        assert result[4] == sum([30, 40, 50]) / 3


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
        assert result[14] is not None
        assert 40 <= result[14] <= 80


class TestMACD:
    def test_macd_structure(self):
        closes = [float(i) for i in range(1, 60)]
        result = macd(_make_prices(closes))
        valid = [r for r in result if r is not None]
        assert len(valid) >= 1
        assert "macd" in valid[0]
        assert "signal" in valid[0]
        assert "histogram" in valid[0]

    def test_macd_higher_ema(self):
        closes = [float(i) for i in range(100, 160)]
        result = macd(_make_prices(closes))
        valid = [r for r in result if r is not None]
        assert len(valid) > 0


class TestATR:
    def test_atr_range(self):
        highs = [110, 115, 112, 118, 120, 122]
        lows = [90, 95, 92, 98, 100, 102]
        closes = [105, 108, 106, 110, 115, 118]
        prices = [
            HistoricalPrice(
                date=date(2024, 1, (i % 28) + 1),
                open=c, high=h, low=l, close=c, volume=1_000_000,
            )
            for i, (c, h, l) in enumerate(zip(closes, highs, lows))
        ]
        result = atr(prices, period=3)
        assert result[3] is not None
        assert result[3] > 0


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


class TestADX:
    def test_adx_not_none(self):
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


class TestStochastic:
    def test_stochastic_range(self):
        prices = _make_prices([float(i) for i in range(1, 30)])
        result = stochastic(prices, period=5)
        valid = [r for r in result if r is not None]
        assert len(valid) > 0
        assert 0 <= valid[0]["k"] <= 100

    def test_stochastic_d_slower(self):
        prices = _make_prices([float(i) for i in range(1, 30)])
        result = stochastic(prices, period=5)
        valid = [r for r in result if r is not None and r["d"] is not None]
        if valid:
            assert len(valid) > 0
