from app.tools.yahoo_finance import get_stock_data
from app.screeners.engine import screen_stock
from app.models.stock import StockData
from app.screeners.engine import ScreeningResult


def fetch_stock(ticker: str) -> StockData | None:
    return get_stock_data(ticker)


def run_screening(data: StockData) -> list[ScreeningResult]:
    return screen_stock(data)
