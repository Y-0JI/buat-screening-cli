from abc import ABC, abstractmethod
from app.models.stock import StockData
from app.models.symbol import SymbolInfo


class Provider(ABC):
    @abstractmethod
    def fetch(self, ticker: str, **kwargs) -> StockData | None:
        ...

    @abstractmethod
    def get_price(self, ticker: str) -> float | None:
        ...

    @abstractmethod
    def list_symbols(self) -> list[SymbolInfo]:
        ...
