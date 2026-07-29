import json
import os
import time
from dataclasses import asdict
from loguru import logger
from app.models.symbol import SymbolInfo
from app.tools import get_provider
from app.validation import normalize

_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "idx_stocks.json")
_DISCOVERY_CACHE = os.path.join(os.path.dirname(__file__), "..", "data", "discovery_cache.json")
_DISCOVERY_TTL = 86400  # 24 jam


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


def get_discovered_tickers() -> list[SymbolInfo]:
    cache_path = _DISCOVERY_CACHE
    try:
        if os.path.exists(cache_path):
            age = time.time() - os.path.getmtime(cache_path)
            if age < _DISCOVERY_TTL:
                with open(cache_path) as f:
                    return [SymbolInfo(**s) for s in json.load(f)]
    except Exception:
        pass

    try:
        p = get_provider()
        symbols = merge_and_dedup([p.list_symbols()])
        if symbols:
            try:
                with open(cache_path, "w") as f:
                    json.dump([asdict(s) for s in symbols], f)
            except Exception:
                pass
            return symbols
    except Exception as e:
        logger.warning(f"Discovery gagal: {e}")

    try:
        with open(_DATA_PATH) as f:
            stocks = json.load(f)
            return [SymbolInfo(ticker=s["ticker"], name=s.get("name"), sector=s.get("sector")) for s in stocks]
    except Exception:
        return []
