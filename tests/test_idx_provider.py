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


def _mock_session(history_data=None, meta_data=None, daily_data=None):
    session = MagicMock()

    def get_side_effect(url, params=None, **kwargs):
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

    session.get.side_effect = get_side_effect
    return session


def test_fetch_success(provider):
    session = _mock_session(
        history_data={
            "replies": [
                {"Date": _d(5), "OpenPrice": 1000, "High": 1010, "Low": 990, "Close": 1005, "Volume": 1000000},
                {"Date": _d(4), "OpenPrice": 1005, "High": 1015, "Low": 995, "Close": 1010, "Volume": 1200000},
            ]
        },
        meta_data={"Profiles": [{"NamaEmiten": "Bank Central Asia Tbk", "Sektor": "Financials"}]},
    )
    with patch.object(provider, "_session", session):
        result = provider.fetch("BBCA")

    assert result is not None
    assert result.info.ticker == "BBCA"
    assert result.info.name == "Bank Central Asia Tbk"
    assert result.info.sector == "Financials"
    assert len(result.history) == 2
    assert result.history[0].close == 1005.0
    assert result.history[0].date == _today() - timedelta(days=5)


def test_fetch_empty_replies(provider):
    session = _mock_session(history_data={"replies": []})
    with patch.object(provider, "_session", session):
        result = provider.fetch("BBCA")
    assert result is None


def test_fetch_no_replies_key(provider):
    session = _mock_session(history_data={})
    with patch.object(provider, "_session", session):
        result = provider.fetch("BBCA")
    assert result is None


def test_get_price(provider):
    session = _mock_session(daily_data={"ClosingPrice": 1005.0})
    with patch.object(provider, "_session", session):
        price = provider.get_price("BBCA")
    assert price == 1005.0


def test_get_price_no_data(provider):
    session = _mock_session(daily_data={})
    with patch.object(provider, "_session", session):
        price = provider.get_price("BBCA")
    assert price is None


def test_fetch_financials_derived_shape(provider):
    session = MagicMock()

    def get_side_effect(url, params=None, **kwargs):
        resp = MagicMock()
        if "GetApiDataPaginated" in url:
            resp.json.return_value = {
                "data": [
                    {"code": "ADRO", "fsDate": "2026-03-31", "eps": 286.52, "bookValue": 3136.99},
                    {"code": "BBCA", "fsDate": "2026-03-31", "eps": 200.0, "bookValue": 1500.0},
                ]
            }
        else:
            resp.json.return_value = {}
        return resp

    session.get.side_effect = get_side_effect
    with patch.object(provider, "_session", session):
        out = provider.fetch_financials("ADRO")
    assert out == {
        "derived": {
            "2026-03-31": {
                "Diluted EPS": 286.52,
                "Book Value": 3136.99,
            }
        }
    }, "harus pick baris yang code-nya cocok dan map ke shape derived"


def test_fetch_financials_empty_when_ticker_not_found(provider):
    session = MagicMock()

    def get_side_effect(url, params=None, **kwargs):
        resp = MagicMock()
        if "GetApiDataPaginated" in url:
            resp.json.return_value = {"data": [{"code": "BBCA", "fsDate": "2026-03-31", "eps": 1, "bookValue": 1}]}
        else:
            resp.json.return_value = {}
        return resp

    session.get.side_effect = get_side_effect
    with patch.object(provider, "_session", session):
        out = provider.fetch_financials("GAGAL")
    assert out == {}



