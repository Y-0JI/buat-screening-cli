from datetime import date
from pydantic import BaseModel


class HistoricalPrice(BaseModel):
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: int


class StockInfo(BaseModel):
    ticker: str
    name: str
    sector: str | None = None
    market_cap: float | None = None
    currency: str = "IDR"


class StockData(BaseModel):
    info: StockInfo
    history: list[HistoricalPrice]
