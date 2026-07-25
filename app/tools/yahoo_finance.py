import time
import yfinance as yf
from loguru import logger
from app.models.stock import HistoricalPrice, StockData, StockInfo
from app.tools.base import StockProvider

_NOT_FOUND_PATTERNS = [
    "possibly delisted",
    "quote not found",
    "http 404",
    "no data found",
    "no data available",
    "symbol may be delisted",
]


def _classify_error(e: Exception) -> str:
    msg = str(e).lower()
    for pat in _NOT_FOUND_PATTERNS:
        if pat in msg:
            return "not_found"
    return "error"


class YahooFinanceProvider(StockProvider):
    def fetch(self, ticker: str, period: str = "6mo") -> StockData | None:
        for attempt in range(3):
            try:
                stock = yf.Ticker(ticker + ".JK")
                info = stock.info
                hist = stock.history(period=period)
                if hist.empty:
                    logger.info(f"Data kosong untuk {ticker}")
                    return None
                stock_info = StockInfo(
                    ticker=ticker.upper(),
                    name=info.get("longName", ticker.upper()),
                    sector=info.get("sector"),
                    market_cap=info.get("marketCap"),
                    currency=info.get("currency", "IDR"),
                )
                history = [
                    HistoricalPrice(
                        date=row.name.date(),
                        open=float(row["Open"]),
                        high=float(row["High"]),
                        low=float(row["Low"]),
                        close=float(row["Close"]),
                        volume=int(row["Volume"]),
                    )
                    for _, row in hist.iterrows()
                ]
                return StockData(info=stock_info, history=history)
            except Exception as e:
                kind = _classify_error(e)
                if kind == "not_found":
                    if attempt == 0:
                        logger.debug(f"Ticker tidak ditemukan {ticker}: {e}")
                    return None
                if attempt < 2:
                    wait = 1 + attempt
                    logger.info(f"Retry {ticker} in {wait}s (attempt {attempt+1}/3): {e}")
                    time.sleep(wait)
                else:
                    logger.warning(f"Gagal fetch {ticker} setelah 3 percobaan: {e}")
                    return None

    def get_price(self, ticker: str) -> float | None:
        data = self.fetch(ticker, period="5d")
        if data and data.history:
            return data.history[-1].close
        return None


provider = YahooFinanceProvider()
