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


def test_merge_empty():
    assert merge_and_dedup([[], []]) == []
    assert merge_and_dedup([]) == []


def test_list_symbols():
    p = YahooFinanceProvider()
    assert p.list_symbols() == []  # Yahoo tidak punya endpoint daftar emiten IDX
    p2 = IDXProvider()
    symbols = p2.list_symbols()
    assert len(symbols) > 0  # IDX baca dari idx_stocks.json
    assert symbols[0].ticker  # ticker tidak boleh kosong


def test_fallback_list_symbols_empty():
    p1 = MagicMock()
    p1.list_symbols.return_value = []
    p2 = MagicMock()
    p2.list_symbols.return_value = []
    fb = FallbackProvider([p1, p2], MagicMock())
    assert fb.list_symbols() == []
