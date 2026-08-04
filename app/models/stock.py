from datetime import date
from pydantic import BaseModel, Field


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
    industry: str | None = None
    exchange: str | None = None
    market: str | None = None
    market_cap: float | None = None
    currency: str = "IDR"
    fundamentals: dict[str, float | str] = Field(default_factory=dict)


class StockData(BaseModel):
    info: StockInfo
    history: list[HistoricalPrice]
