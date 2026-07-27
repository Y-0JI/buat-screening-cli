from dataclasses import dataclass


@dataclass
class SymbolInfo:
    ticker: str
    name: str | None = None
    sector: str | None = None
