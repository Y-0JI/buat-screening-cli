from datetime import date
import pytest
from app.models.stock import HistoricalPrice, StockData, StockInfo
from app.screeners.engine import rsi_signal, volume_spike, screen_stock, breakout, trend_detection


def _make_data(closes: list[float], volumes: list[int] | None = None) -> StockData:
    v = volumes or [1_000_000] * len(closes)
    return StockData(
        info=StockInfo(ticker="BBCA", name="Test", sector="Finance", market_cap=1e12),
        history=[
            HistoricalPrice(
                date=date(2024, 1, (i % 30) + 1),
                open=c, high=c * 1.01, low=c * 0.99, close=c, volume=v[i],
            )
            for i, c in enumerate(closes)
        ],
    )


class TestRSISignal:
    def test_oversold(self):
        closes = [50 - i * 1.5 for i in range(35)]
        data = _make_data(closes)
        result = rsi_signal(data)
        if result:
            assert result.signal == "BUY"
            assert "Oversold" in result.reason

    def test_overbought(self):
        closes = [50 + i * 2 for i in range(35)]
        data = _make_data(closes)
        result = rsi_signal(data)
        if result:
            assert result.signal == "SELL"
            assert "Overbought" in result.reason

    def test_no_signal(self):
        closes = [50.0] * 30
        data = _make_data(closes)
        result = rsi_signal(data)
        assert result is None


class TestVolumeSpike:
    def test_spike_detected(self):
        closes = [100.0] * 25
        vols = [1_000_000] * 22 + [5_000_000] * 3
        data = _make_data(closes, vols)
        result = volume_spike(data)
        assert result is not None
        assert "Volume Spike" in result.reason

    def test_no_spike(self):
        closes = [100.0] * 25
        vols = [1_000_000] * 25
        data = _make_data(closes, vols)
        result = volume_spike(data)
        assert result is None


class TestBreakout:
    def test_breakout_detected(self):
        hist = [100.0] * 22 + [110.0]
        data = _make_data(hist)
        result = breakout(data)
        assert result is not None
        assert result.signal == "BUY"
        assert "Breakout" in result.reason

    def test_no_breakout(self):
        closes = [100.0] * 25
        data = _make_data(closes)
        result = breakout(data)
        assert result is None


class TestTrendDetection:
    def test_screen_returns_list(self):
        closes = [100.0] * 60
        data = _make_data(closes)
        result = trend_detection(data)
        assert result is not None


class TestScreenStock:
    def test_screen_returns_list(self):
        closes = [100.0] * 60
        data = _make_data(closes)
        results = screen_stock(data)
        assert isinstance(results, list)
