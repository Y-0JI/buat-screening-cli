from unittest.mock import patch, MagicMock
from datetime import date, timedelta
import pytest
from app.tools.idx import IDXProvider


@pytest.fixture
def provider():
    return IDXProvider()


def _today():
    return date.today()


def _d(offset):
    return (_today() - timedelta(days=offset)).isoformat()


def _mock_client(history_data=None, meta_data=None, daily_data=None):
    client = MagicMock()

    def get_side_effect(url, params=None):
        resp = MagicMock()
        if "GetTradingInfoSS" in url:
            resp.json.return_value = history_data or {}
        elif "GetCompanyProfilesDetail" in url:
            resp.json.return_value = meta_data or {}
        elif "GetTradingInfoDaily" in url:
            resp.json.return_value = daily_data or {}
        else:
            resp.json.return_value = {}
        return resp

    client.get.side_effect = get_side_effect
    return client


def test_fetch_success(provider):
    client = _mock_client(
        history_data={
            "replies": [
                {"Date": _d(5), "OpenPrice": 1000, "High": 1010, "Low": 990, "Close": 1005, "Volume": 1000000},
                {"Date": _d(4), "OpenPrice": 1005, "High": 1015, "Low": 995, "Close": 1010, "Volume": 1200000},
            ]
        },
        meta_data={"Profiles": [{"NamaEmiten": "Bank Central Asia Tbk", "Sektor": "Financials"}]},
    )
    with patch.object(provider, "_client", client), patch.object(provider, "_ensure_session"):
        result = provider.fetch("BBCA")

    assert result is not None
    assert result.info.ticker == "BBCA"
    assert result.info.name == "Bank Central Asia Tbk"
    assert result.info.sector == "Financials"
    assert len(result.history) == 2
    assert result.history[0].close == 1005.0
    assert result.history[0].date == _today() - timedelta(days=5)


def test_fetch_empty_replies(provider):
    client = _mock_client(history_data={"replies": []})
    with patch.object(provider, "_client", client), patch.object(provider, "_ensure_session"):
        result = provider.fetch("BBCA")
    assert result is None


def test_fetch_no_replies_key(provider):
    client = _mock_client(history_data={})
    with patch.object(provider, "_client", client), patch.object(provider, "_ensure_session"):
        result = provider.fetch("BBCA")
    assert result is None


def test_get_price(provider):
    client = _mock_client(daily_data={"ClosingPrice": 1005.0})
    with patch.object(provider, "_client", client), patch.object(provider, "_ensure_session"):
        price = provider.get_price("BBCA")
    assert price == 1005.0


def test_get_price_no_data(provider):
    client = _mock_client(daily_data={})
    with patch.object(provider, "_client", client), patch.object(provider, "_ensure_session"):
        price = provider.get_price("BBCA")
    assert price is None


def test_provider_implements_stock_provider(provider):
    from app.tools.base import StockProvider
    assert isinstance(provider, StockProvider)
