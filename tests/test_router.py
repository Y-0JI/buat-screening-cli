from unittest.mock import patch
from app.router.engine import fetch_stock, run_screening


def test_fetch_stock():
    with patch("app.router.engine.get_stock_data") as mock_get:
        mock_get.return_value = "stock_data"
        result = fetch_stock("BBCA")
        assert result == "stock_data"
        mock_get.assert_called_once_with("BBCA")


def test_fetch_stock_none():
    with patch("app.router.engine.get_stock_data") as mock_get:
        mock_get.return_value = None
        result = fetch_stock("INVALID")
        assert result is None
