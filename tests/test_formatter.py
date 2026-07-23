from datetime import date
from app.models.stock import HistoricalPrice, StockData, StockInfo
from app.models.analysis import AIAnalysis
from app.screeners.engine import ScreeningResult
from app.cli.formatter import print_screening_results, print_stock_header, print_price_info, print_ai_analysis


def test_print_screening_results_empty():
    print_screening_results([])


def test_print_stock_header():
    data = StockData(
        info=StockInfo(ticker="BBCA", name="Test Bank", sector="Finance", market_cap=1e12),
        history=[],
    )
    print_stock_header(data)


def test_print_price_info():
    data = StockData(
        info=StockInfo(ticker="BBCA", name="Test"),
        history=[
            HistoricalPrice(date=date(2024, 1, 1), open=100.0, high=101.0, low=99.0, close=100.5, volume=1_000_000),
            HistoricalPrice(date=date(2024, 1, 2), open=101.0, high=102.0, low=100.0, close=101.5, volume=1_500_000),
        ],
    )
    print_price_info(data)


def test_print_ai_analysis():
    result = AIAnalysis(
        ticker="BBCA",
        summary="Performa saham baik",
        key_metrics={"RSI": "55", "MACD": "bullish"},
        risks=["Volatilitas tinggi"],
        conclusion="Layak dibeli",
    )
    print_ai_analysis(result)


def test_print_ai_analysis_empty():
    result = AIAnalysis(ticker="BBCA", summary="")
    print_ai_analysis(result)
