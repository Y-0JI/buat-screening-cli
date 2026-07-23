from unittest.mock import patch, MagicMock
from datetime import date
import pandas as pd
import pytest
from app.tools.yahoo_finance import get_stock_data, get_current_price


@pytest.fixture
def mock_stock_data():
    mock_ticker = MagicMock()
    mock_ticker.info = {
        "longName": "PT Bank Central Asia Tbk",
        "sector": "Financial Services",
        "marketCap": 1_000_000_000_000,
        "currency": "IDR",
    }
    dates = pd.date_range("2024-01-01", periods=5, freq="D")
    mock_ticker.history.return_value = pd.DataFrame({
        "Open": [1000.0] * 5,
        "High": [1010.0] * 5,
        "Low": [990.0] * 5,
        "Close": [1005.0] * 5,
        "Volume": [1_000_000] * 5,
    }, index=dates)
    return mock_ticker


def test_get_stock_data_success(mock_stock_data):
    with patch("app.tools.yahoo_finance.yf.Ticker", return_value=mock_stock_data):
        result = get_stock_data("BBCA")

    assert result is not None
    assert result.info.ticker == "BBCA"
    assert result.info.name == "PT Bank Central Asia Tbk"
    assert result.info.sector == "Financial Services"
    assert len(result.history) == 5
    assert result.history[0].close == 1005.0


def test_get_stock_data_empty_history():
    mock_ticker = MagicMock()
    mock_ticker.info = {"longName": "Test"}
    mock_ticker.history.return_value = pd.DataFrame()

    with patch("app.tools.yahoo_finance.yf.Ticker", return_value=mock_ticker):
        result = get_stock_data("TEST")

    assert result is None


def test_get_current_price(mock_stock_data):
    with patch("app.tools.yahoo_finance.yf.Ticker", return_value=mock_stock_data):
        price = get_current_price("BBCA")

    assert price == 1005.0


def test_get_current_price_empty():
    mock_ticker = MagicMock()
    mock_ticker.info = {}
    mock_ticker.history.return_value = pd.DataFrame()

    with patch("app.tools.yahoo_finance.yf.Ticker", return_value=mock_ticker):
        price = get_current_price("TEST")

    assert price is None
