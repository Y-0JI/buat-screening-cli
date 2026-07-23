import yfinance as yf
from app.models.stock import HistoricalPrice, StockData, StockInfo
from app.tools.base import StockProvider


class YahooFinanceProvider(StockProvider):
    def fetch(self, ticker: str, period: str = "6mo") -> StockData | None:
        try:
            stock = yf.Ticker(ticker + ".JK")
            info = stock.info
            hist = stock.history(period=period)
            if hist.empty:
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
        except Exception:
            return None

    def get_price(self, ticker: str) -> float | None:
        data = self.fetch(ticker, period="5d")
        if data and data.history:
            return data.history[-1].close
        return None


provider = YahooFinanceProvider()
