from unittest.mock import patch
from app.router.engine import fetch_stock


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
