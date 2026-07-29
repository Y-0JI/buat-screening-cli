from app.models.symbol import SymbolInfo
from app.services.stock_list import merge_and_dedup
from app.tools.yahoo_finance import YahooFinanceProvider
from app.tools.idx import IDXProvider
from app.tools import FallbackProvider
from unittest.mock import MagicMock


def test_merge_no_duplicates():
    a = [SymbolInfo(ticker="BBCA"), SymbolInfo(ticker="BBRI")]
    b = [SymbolInfo(ticker="ADRO"), SymbolInfo(ticker="ANTM")]
    result = merge_and_dedup([a, b])
    assert len(result) == 4


def test_merge_with_duplicates():
    a = [SymbolInfo(ticker="BBCA"), SymbolInfo(ticker="BBRI")]
    b = [SymbolInfo(ticker="BBCA"), SymbolInfo(ticker="ADRO")]
    result = merge_and_dedup([a, b])
    assert len(result) == 3


def test_merge_filters_invalid_format():
    valid = [SymbolInfo(ticker="BBCA"), SymbolInfo(ticker="BBRI"), SymbolInfo(ticker="ADRO"), SymbolInfo(ticker="A2")]
    invalid = [SymbolInfo(ticker=""), SymbolInfo(ticker="TOOLONGTICKER"), SymbolInfo(ticker="weird!"), SymbolInfo(ticker="abc 123")]
    result = merge_and_dedup([valid + invalid])
    assert [s.ticker for s in result] == ["BBCA", "BBRI", "ADRO", "A2"]


def test_merge_empty():
    assert merge_and_dedup([[], []]) == []
    assert merge_and_dedup([]) == []


def test_list_symbols_yahoo():
    p = YahooFinanceProvider()
    assert p.list_symbols() == []


def test_list_symbols_idx_success():
    p2 = IDXProvider()
    mock_resp = MagicMock()
    mock_resp.json.return_value = [
        {"KodeEmiten": "BBCA", "NamaEmiten": "Bank BCA", "Sektor": "Financials"},
        {"KodeEmiten": "BBRI", "NamaEmiten": "Bank BRI", "Sektor": "Financials"},
    ]
    p2._session = MagicMock()
    p2._session.get.return_value = mock_resp
    symbols = p2.list_symbols()
    assert len(symbols) == 2
    assert symbols[0].ticker == "BBCA"
    assert symbols[0].name == "Bank BCA"
    assert symbols[1].sector == "Financials"


def test_list_symbols_idx_api_error():
    p2 = IDXProvider()
    p2._session = MagicMock()
    p2._session.get.side_effect = Exception("403 Forbidden")
    symbols = p2.list_symbols()
    assert symbols == []


def test_fallback_list_symbols_empty():
    p1 = MagicMock()
    p1.list_symbols.return_value = []
    p2 = MagicMock()
    p2.list_symbols.return_value = []
    fb = FallbackProvider([p1, p2], MagicMock())
    assert fb.list_symbols() == []


def test_fallback_list_symbols_skip_failed():
    p1 = MagicMock()
    p1.list_symbols.side_effect = Exception("gagal")
    p2 = MagicMock()
    p2.list_symbols.return_value = [SymbolInfo(ticker="BBCA")]
    fb = FallbackProvider([p1, p2], MagicMock())
    symbols = fb.list_symbols()
    assert len(symbols) == 1
    assert symbols[0].ticker == "BBCA"
