import json
import os
from loguru import logger

_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "idx_stocks.json")
_cached_universe: list[dict] | None = None


def _load_from_idx() -> list[dict] | None:
    try:
        from app.tools.idx import IDXProvider
        provider = IDXProvider()
        companies = provider.fetch_universe()
        if companies:
            return companies
    except Exception as e:
        logger.debug(f"Gagal load universe dari IDX: {e}")
    return None


def _load_from_json() -> list[dict]:
    with open(_DATA_PATH) as f:
        return json.load(f)


def _load() -> list[dict]:
    global _cached_universe
    if _cached_universe is not None:
        return _cached_universe

    stocks = _load_from_idx()
    if not stocks:
        logger.info("Fallback ke idx_stocks.json untuk stock universe")
        stocks = _load_from_json()

    _cached_universe = stocks
    return stocks


def refresh() -> None:
    global _cached_universe
    _cached_universe = None


def get_all() -> list[dict]:
    stocks = _load()
    if not stocks:
        return []
    if "valid" in stocks[0]:
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
