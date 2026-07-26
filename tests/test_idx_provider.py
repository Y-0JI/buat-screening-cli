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


def _mock_json_response(data, status=200, content_type="application/json", headers=None):
    resp = MagicMock()
    resp.status_code = status
    resp.headers = headers or {"content-type": content_type}
    resp.json.return_value = data
    resp.text = "<html>blocked</html>" if status != 200 else "{}"
    resp.history = []
    resp.url = "http://test.url"
    return resp


def test_fetch_universe_success(provider):
    mock_data = [
        {"KodeEmiten": "BBCA", "NamaEmiten": "Bank Central Asia Tbk", "Sektor": "Financials"},
        {"KodeEmiten": "BBRI", "NamaEmiten": "Bank Rakyat Indonesia Tbk", "Sektor": "Financials"},
        {"KodeEmiten": "TLKM", "NamaEmiten": "Telkom Indonesia Tbk", "Sektor": "Communication Services"},
    ]
    client = MagicMock()
    client.get.return_value = _mock_json_response(mock_data)
    with patch.object(provider, "_client", client), patch.object(provider, "_ensure_session"):
        result = provider.fetch_universe()

    assert len(result) == 3
    assert result[0] == {"ticker": "BBCA", "name": "Bank Central Asia Tbk", "sector": "Financials", "valid": True}
    assert result[1]["ticker"] == "BBRI"
    assert result[2]["ticker"] == "TLKM"


def test_fetch_universe_wraps_in_list(provider):
    mock_data = {"replies": [
        {"KodeEmiten": "BBCA", "NamaEmiten": "Bank Central Asia Tbk", "Sektor": "Financials"},
    ]}
    client = MagicMock()
    client.get.return_value = _mock_json_response(mock_data)
    with patch.object(provider, "_client", client), patch.object(provider, "_ensure_session"):
        result = provider.fetch_universe()

    assert len(result) == 1
    assert result[0]["ticker"] == "BBCA"


def test_fetch_universe_empty_response(provider):
    client = MagicMock()
    client.get.return_value = _mock_json_response({})
    with patch.object(provider, "_client", client), patch.object(provider, "_ensure_session"):
        result = provider.fetch_universe()
    assert result == []


def test_fetch_universe_no_ticker_skipped(provider):
    mock_data = [
        {"NamaEmiten": "No Ticker Here", "Sektor": "Finance"},
    ]
    client = MagicMock()
    client.get.return_value = _mock_json_response(mock_data)
    with patch.object(provider, "_client", client), patch.object(provider, "_ensure_session"):
        result = provider.fetch_universe()
    assert result == []


def test_fetch_universe_handles_http_error(provider):
    client = MagicMock()
    client.get.side_effect = Exception("HTTP 500")
    with patch.object(provider, "_client", client), patch.object(provider, "_ensure_session"):
        result = provider.fetch_universe()
    assert result == []


def test_fetch_universe_non_json_response(provider):
    resp = _mock_json_response({}, status=403, content_type="text/html")
    resp.text = "<html>Access Denied</html>"
    resp.headers = {"content-type": "text/html", "server": "cloudflare"}
    client = MagicMock()
    client.get.return_value = resp
    with patch.object(provider, "_client", client), patch.object(provider, "_ensure_session"):
        result = provider.fetch_universe()
    assert result == []
