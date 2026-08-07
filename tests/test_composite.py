from datetime import date
from unittest.mock import patch

from app.models.stock import HistoricalPrice, StockData, StockInfo
from app.screeners.engine import ScreeningResult
from app.router.composite import build_composite


def _mock_stock(price: float, prev: float) -> StockData:
    return StockData(
        info=StockInfo(ticker="BBCA", name="Bank BCA", sector="Financials"),
        history=[
            HistoricalPrice(date=date(2024, 1, 1), open=prev, high=prev, low=prev, close=prev, volume=0),
            HistoricalPrice(date=date(2024, 1, 2), open=price, high=price, low=price, close=price, volume=0),
        ],
    )


def _mocks(price: float = 100.0, prev: float = 90.0):
    stock = _mock_stock(price, prev)
    ctx = {
        "name": "Bank BCA",
        "price": price,
        "change": "+11.11%",
        "sector": "Banking",
        "indicators": "RSI=60.0 | SMA20=95",
    }
    patches = [
        patch("app.router.composite.fetch_stock", return_value=stock),
        patch("app.router.composite.build_context", return_value=ctx),
        patch("app.router.composite.run_screening", return_value=[
            ScreeningResult(ticker="BBCA", signal="BUY", reason="Golden Cross", confidence=0.8),
        ]),
        patch("app.router.composite.provider"),
        patch("app.router.composite.analyze_with_ai"),
    ]
    started = [p.start() for p in patches]
    return patches, started


def _stop(patches):
    for p in patches:
        p.stop()


class _FakeAI:
    def __init__(self, summary: str):
        self.summary = summary


def test_happy_path_all_blocks_available():
    patches, started = _mocks()
    started[3].fetch_financials.return_value = {"financials": {}}
    started[4].return_value = _FakeAI("Analisis naratif")
    try:
        r = build_composite("BBCA")
        assert r.ticker == "BBCA"
        assert r.name == "Bank BCA"
        assert r.blocks["quote"].status == "available"
        assert r.blocks["quote"].data["price"] == 100.0
        assert r.blocks["stats"].status == "available"
        assert r.blocks["stats"].data["indicators"] == "RSI=60.0 | SMA20=95"
        assert r.blocks["signal"].status == "available"
        assert r.blocks["signal"].data["signals"][0]["signal"] == "BUY"
        assert r.blocks["narrative"].status == "available"
        assert r.blocks["narrative"].data["summary"] == "Analisis naratif"
    finally:
        _stop(patches)


def test_fetch_fails_all_unavailable():
    patches, started = _mocks()
    started[0].return_value = None
    try:
        r = build_composite("BBCA")
        assert all(b.status == "unavailable" for b in r.blocks.values())
    finally:
        _stop(patches)


def test_financials_failure_stats_partial_others_ok():
    patches, started = _mocks()
    started[3].fetch_financials.side_effect = RuntimeError("network down")
    started[4].return_value = _FakeAI("Analisis naratif")
    try:
        r = build_composite("BBCA")
        assert r.blocks["stats"].status == "partial"
        assert r.blocks["stats"].data.get("indicators") == "RSI=60.0 | SMA20=95"
        assert r.blocks["stats"].error
        assert r.blocks["quote"].status == "available"
        assert r.blocks["signal"].status == "available"
        assert r.blocks["narrative"].status == "available"
    finally:
        _stop(patches)


def test_narrative_failure_only_narrative_down():
    patches, started = _mocks()
    started[4].side_effect = RuntimeError("LLM down")
    try:
        r = build_composite("BBCA")
        assert r.blocks["narrative"].status == "unavailable"
        assert r.blocks["narrative"].error
        assert r.blocks["quote"].status == "available"
        assert r.blocks["stats"].status == "available"
        assert r.blocks["signal"].status == "available"
    finally:
        _stop(patches)


def test_stats_merge_first_wins_keeps_existing_key():
    patches, started = _mocks()
    started[3].fetch_financials.return_value = {"financials": {"2024-12-31": {"Total Revenue": 1e12}}}
    started[4].return_value = _FakeAI("x")
    ctx = patch("app.router.composite.build_context", return_value={
        "name": "Bank BCA", "price": 100.0, "change": "+1%", "sector": "Banking",
        "indicators": "RSI=60.0 | SMA20=95",
    })
    ctx.start()
    try:
        r = build_composite("BBCA")
        stats_data = r.blocks["stats"].data
        assert stats_data.get("indicators") == "RSI=60.0 | SMA20=95"
        assert "revenue" in stats_data
    finally:
        _stop(patches)
        _stop([ctx])