from datetime import date
from io import StringIO
from rich.console import Console
from app.models.stock import HistoricalPrice, StockData, StockInfo
from app.models.analysis import AIAnalysis
from app.screeners.engine import ScreeningResult
from app.cli.formatter import print_screening_results, print_stock_header, print_price_info, print_ai_analysis, print_bulk_screening


def _capture(fn, *args, **kwargs) -> str:
    console = Console(file=StringIO(), width=120)
    import app.cli.formatter as f
    original = f.console
    f.console = console
    try:
        fn(*args, **kwargs)
        return console.file.getvalue()
    finally:
        f.console = original


def test_print_screening_results_empty_snapshot():
    output = _capture(print_screening_results, [])
    assert "Tidak ada" in output


def test_print_screening_results_with_data_snapshot():
    results = [
        ScreeningResult(ticker="BBCA", signal="BUY", reason="Golden Cross", confidence=0.8),
        ScreeningResult(ticker="BBRI", signal="SELL", reason="RSI Overbought", confidence=0.7),
    ]
    output = _capture(print_screening_results, results)
    assert "BBCA" not in output
    assert "Golden Cross" in output
    assert "RSI Overbought" in output


def test_print_stock_header_snapshot():
    data = StockData(
        info=StockInfo(ticker="BBCA", name="Test Bank", sector="Finance", market_cap=1e12),
        history=[],
    )
    output = _capture(print_stock_header, data)
    assert "BBCA" in output
    assert "Test Bank" in output


def test_print_price_info_snapshot():
    data = StockData(
        info=StockInfo(ticker="BBCA", name="Test"),
        history=[
            HistoricalPrice(date=date(2024, 1, 1), open=100.0, high=101.0, low=99.0, close=100.5, volume=1_000_000),
            HistoricalPrice(date=date(2024, 1, 2), open=101.0, high=102.0, low=100.0, close=101.5, volume=1_500_000),
        ],
    )
    output = _capture(print_price_info, data)
    assert "Harga" in output
    assert "1,500,000" in output


def test_print_ai_analysis_snapshot():
    result = AIAnalysis(
        ticker="BBCA",
        summary="Performa saham baik",
        key_metrics={"RSI": "55", "MACD": "bullish"},
        risks=["Volatilitas tinggi"],
        conclusion="Layak dibeli",
    )
    output = _capture(print_ai_analysis, result)
    assert "Ringkasan" in output
    assert "Performa saham baik" in output
    assert "Risiko" in output
    assert "Layak dibeli" in output


def test_ai_analysis_empty_snapshot():
    result = AIAnalysis(ticker="BBCA", summary="")
    output = _capture(print_ai_analysis, result)
    assert "BBCA" in output


def test_bulk_screening_snapshot():
    from app.screeners.engine import ScreeningResult
    results = [
        {
            "ticker": "BBCA",
            "name": "Bank BCA",
            "sector": "Financials",
            "price": 10250,
            "top_signal": ScreeningResult(ticker="BBCA", signal="BUY", reason="Golden Cross", confidence=0.8),
        }
    ]
    output = _capture(print_bulk_screening, results)
    assert "BBCA" in output
    assert "BUY" in output
    assert "Bank BCA" in output
