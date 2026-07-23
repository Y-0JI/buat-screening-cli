from abc import ABC, abstractmethod
from app.models.stock import StockData


class StockProvider(ABC):
    @abstractmethod
    def fetch(self, ticker: str, period: str = "6mo") -> StockData | None: ...

    @abstractmethod
    def get_price(self, ticker: str) -> float | None: ...
