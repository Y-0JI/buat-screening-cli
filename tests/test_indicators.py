from datetime import date
import pytest
from app.models.stock import HistoricalPrice
from app.indicators.engine import sma, ema, rsi, macd, bollinger


def _make_prices(closes: list[float]) -> list[HistoricalPrice]:
    return [
        HistoricalPrice(
            date=date(2024, 1, (i % 30) + 1),
            open=c, high=c, low=c * 0.99, close=c, volume=1_000_000,
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



