from unittest.mock import patch
from app.router.engine import fetch_stock, bulk_losers


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
        mock_provider.get_price.side_effect = {"BBCA": 100.0, "BBRI": 50.0}.get
        results = bulk_losers(["BBCA", "BBRI"])
        assert len(results) == 2
        assert results[0]["ticker"] == "BBRI"
        assert results[0]["price"] == 50.0
