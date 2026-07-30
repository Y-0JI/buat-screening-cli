import logging
import random
import time
import yfinance as yf
from loguru import logger

logging.getLogger("yfinance").setLevel(logging.CRITICAL)
from app.models.stock import HistoricalPrice, StockData, StockInfo
from app.models.symbol import SymbolInfo
from app.tools.base import Provider, _classify_error
from app.tools.registry import ProviderRegistry

_last_rate_limit: list[float] = [0.0]  # mutable for shared cooldown across modules
_invalid_tickers: set[str] = set()  # session cache ticker delisted


class YahooFinanceProvider(Provider):
    def fetch(self, ticker: str, period: str = "6mo", need_profile: bool = True) -> StockData | None:
        if ticker.upper() in _invalid_tickers:
            logger.debug(f"Skip {ticker}: already in invalid cache")
            return None
        cooldown = time.time() - _last_rate_limit[0]
        if cooldown < 15:
            time.sleep(15 - cooldown)
        time.sleep(random.uniform(0.3, 0.8))
        for attempt in range(3):
            try:
                stock = yf.Ticker(ticker + ".JK")
                if need_profile:
                    info = stock.info
                    stock_info = StockInfo(
                        ticker=ticker.upper(),
                        name=info.get("longName", ticker.upper()),
                        sector=info.get("sector"),
                        industry=info.get("industry"),
                        exchange=info.get("exchange"),
                        market=info.get("market"),
                        market_cap=info.get("marketCap"),
                        currency=info.get("currency", "IDR"),
                    )
                else:
                    stock_info = StockInfo(ticker=ticker.upper(), name=ticker.upper())
                hist = stock.history(period=period)
                if hist.empty:
                    logger.debug(f"Data kosong untuk {ticker}")
                    return None
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
                    _invalid_tickers.add(ticker.upper())
                    if attempt == 0:
                        logger.debug(f"Ticker tidak ditemukan {ticker}: {e}")
                    return None
                if kind == "rate_limited":
                    _last_rate_limit[0] = time.time()
                    delay = random.uniform(10, 30)
                    logger.warning(f"Rate limited {ticker}, cooling {delay:.0f}s (attempt {attempt+1}/3)")
                    time.sleep(delay)
                elif attempt < 2:
                    delay = (1 + attempt) * random.uniform(0.5, 1.5)
                    logger.debug(f"Retry {ticker} in {delay:.1f}s (attempt {attempt+1}/3): {e}")
                    time.sleep(delay)
                else:
                    logger.warning(f"Gagal fetch {ticker} setelah 3 percobaan: {e}")
                    return None

    def get_price(self, ticker: str) -> float | None:
        if ticker.upper() in _invalid_tickers:
            return None
        data = self.fetch(ticker, period="5d")
        if data and data.history:
            return data.history[-1].close
        return None

    def list_symbols(self) -> list[SymbolInfo]:
        """Yahoo Finance tidak punya endpoint daftar emiten IDX yang reliable."""
        return []


ProviderRegistry.register("yahoo", YahooFinanceProvider)
