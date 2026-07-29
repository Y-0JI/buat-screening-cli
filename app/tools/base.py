from abc import ABC, abstractmethod
from app.models.stock import StockData
from app.models.symbol import SymbolInfo

_RATE_LIMITED_PATTERNS = ["rate limit", "too many requests", "429"]
_NOT_FOUND_PATTERNS = ["not found", "no data", "delisted", "404"]


def _classify_error(e: Exception) -> str:
    msg = str(e).lower()
    for pat in _RATE_LIMITED_PATTERNS:
        if pat in msg:
            return "rate_limited"
    for pat in _NOT_FOUND_PATTERNS:
        if pat in msg:
            return "not_found"
    return "error"


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
