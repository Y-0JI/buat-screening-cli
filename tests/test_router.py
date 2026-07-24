from unittest.mock import patch
from app.models.stock import HistoricalPrice, StockData, StockInfo
from app.router.engine import fetch_stock, bulk_losers, bulk_gainers
from datetime import date


def _mock_stock(price: float, prev: float) -> StockData:
    return StockData(
        info=StockInfo(ticker="TEST", name="Test", sector=None, market_cap=None),
        history=[
            HistoricalPrice(date=date(2024, 1, 1), open=prev, high=prev, low=prev, close=prev, volume=0),
            HistoricalPrice(date=date(2024, 1, 2), open=price, high=price, low=price, close=price, volume=0),
        ],
    )


def test_fetch_stock():
    with patch("app.router.engine.provider") as mock_provider:
        mock_provider.fetch.return_value = "stock_data"
        result = fetch_stock("BBCA")
        assert result == "stock_data"
        mock_provider.fetch.assert_called_once_with("BBCA")


def test_fetch_stock_none():
    with patch("app.router.engine.provider") as mock_provider:
        mock_provider.fetch.return_value = None
        result = fetch_stock("INVALID")
        assert result is None


def test_bulk_losers():
    with patch("app.router.engine.provider") as mock_provider:
        mock_provider.fetch.side_effect = lambda t, period="5d": {
            "BBCA": _mock_stock(price=100.0, prev=110.0),
            "BBRI": _mock_stock(price=50.0, prev=60.0),
        }.get(t)
        results = bulk_losers(["BBCA", "BBRI"])
        assert len(results) == 2
        assert results[0]["ticker"] == "BBRI"
        assert results[0]["change"] < results[1]["change"]


def test_bulk_gainers():
    with patch("app.router.engine.provider") as mock_provider:
        mock_provider.fetch.side_effect = lambda t, period="5d": {
            "BBCA": _mock_stock(price=100.0, prev=110.0),
            "BBRI": _mock_stock(price=50.0, prev=40.0),
        }.get(t)
        results = bulk_gainers(["BBCA", "BBRI"])
        assert len(results) == 2
        assert results[0]["ticker"] == "BBRI"
        assert results[0]["change"] > results[1]["change"]
