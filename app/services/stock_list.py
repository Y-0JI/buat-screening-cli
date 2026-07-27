import json
import os
from loguru import logger
from app.models.symbol import SymbolInfo
from app.validation import normalize

_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "idx_stocks.json")


def _load() -> list[dict]:
    with open(_DATA_PATH) as f:
        return json.load(f)


def get_all() -> list[dict]:
    stocks = _load()
    if stocks and "valid" in stocks[0]:
        return [s for s in stocks if s.get("valid", True)]
    return stocks


def search(query: str) -> list[dict]:
    q = query.lower()
    stocks = _load()
    results = [s for s in stocks if q in s["ticker"].lower() or q in s["name"].lower()]
    if results and "valid" in results[0]:
        return [s for s in results if s.get("valid", True)]
    return results


def count() -> int:
    return len(get_all())

_cache: dict[str, dict] | None = None

def _by_ticker() -> dict[str, dict]:
    global _cache
    if _cache is None:
        _cache = {s["ticker"]: s for s in get_all()}
    return _cache

def resolve_name(ticker: str) -> str | None:
    s = _by_ticker().get(normalize(ticker))
    return s["name"] if s else None

def resolve_sector(ticker: str) -> str | None:
    s = _by_ticker().get(normalize(ticker))
    return s.get("sector") if s else None


def merge_and_dedup(sources: list[list[SymbolInfo]]) -> list[SymbolInfo]:
    seen: dict[str, SymbolInfo] = {}
    for symbols in sources:
        for sym in symbols:
            t = normalize(sym.ticker) if sym.ticker else ""
            if not t:
                continue
            if t not in seen:
                seen[t] = sym
    return list(seen.values())
