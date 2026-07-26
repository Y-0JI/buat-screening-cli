import json
import os

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
