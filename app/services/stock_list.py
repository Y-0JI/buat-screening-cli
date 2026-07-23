import json
import os

_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "idx_stocks.json")


def _load() -> list[dict]:
    with open(_DATA_PATH) as f:
        return json.load(f)


def get_all() -> list[dict]:
    return _load()


def search(query: str) -> list[dict]:
    q = query.lower()
    return [s for s in _load() if q in s["ticker"].lower() or q in s["name"].lower()]


def count() -> int:
    return len(_load())
