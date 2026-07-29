import json
import os
from datetime import datetime, timezone

from app.models.watchlist import Watchlist, WatchlistEntry
from app.validation import normalize

_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "watchlists.json")


def _load() -> list[dict]:
    if not os.path.exists(_DATA_PATH):
        return []
    with open(_DATA_PATH) as f:
        return json.load(f)


def _save(data: list[dict]) -> None:
    with open(_DATA_PATH, "w") as f:
        json.dump(data, f, indent=2)


def _to_model(d: dict) -> Watchlist:
    return Watchlist(**d)


def _to_dict(w: Watchlist) -> dict:
    return w.model_dump()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_default(data: list[dict]) -> list[dict]:
    if not data:
        w = Watchlist(name="Watchlist Saya")
        data.append(_to_dict(w))
        _save(data)
    return data


def create(name: str) -> Watchlist:
    data = _load()
    data = _ensure_default(data)
    names = {d["name"] for d in data}
    if name in names:
        raise ValueError(f"Watchlist '{name}' sudah ada")
    w = Watchlist(name=name)
    data.append(_to_dict(w))
    _save(data)
    return w


def rename(wl_id: str, new_name: str) -> Watchlist:
    data = _load()
    for d in data:
        if d["name"] == new_name:
            raise ValueError(f"Watchlist '{new_name}' sudah ada")
    for d in data:
        if d["id"] == wl_id:
            d["name"] = new_name
            d["updated_at"] = _now()
            _save(data)
            return _to_model(d)
    raise ValueError(f"Watchlist id '{wl_id}' tidak ditemukan")


def delete(wl_id: str) -> None:
    data = _load()
    before = len(data)
    data = [d for d in data if d["id"] != wl_id]
    if len(data) == before:
        raise ValueError(f"Watchlist id '{wl_id}' tidak ditemukan")
    data = _ensure_default(data)
    _save(data)


def list_all() -> list[Watchlist]:
    data = _load()
    data = _ensure_default(data)
    return [_to_model(d) for d in data]


def get_by_id(wl_id: str) -> Watchlist:
    data = _load()
    for d in data:
        if d["id"] == wl_id:
            return _to_model(d)
    raise ValueError(f"Watchlist id '{wl_id}' tidak ditemukan")


def add_symbol(wl_id: str, ticker: str) -> Watchlist:
    t = normalize(ticker)
    data = _load()
    for d in data:
        if d["id"] != wl_id:
            continue
        existing = {e["ticker"] for e in d["entries"]}
        if t in existing:
            raise ValueError(f"'{t}' sudah ada di watchlist")
        pos = len(d["entries"])
        entry = WatchlistEntry(ticker=t, added_at=_now(), position=pos)
        d["entries"].append(entry.model_dump())
        d["updated_at"] = _now()
        _save(data)
        return _to_model(d)
    raise ValueError(f"Watchlist id '{wl_id}' tidak ditemukan")


def remove_symbol(wl_id: str, ticker: str) -> Watchlist:
    t = normalize(ticker)
    data = _load()
    for d in data:
        if d["id"] != wl_id:
            continue
        before = len(d["entries"])
        d["entries"] = [e for e in d["entries"] if e["ticker"] != t]
        if len(d["entries"]) == before:
            raise ValueError(f"'{t}' tidak ditemukan di watchlist")
        for i, e in enumerate(d["entries"]):
            e["position"] = i
        d["updated_at"] = _now()
        _save(data)
        return _to_model(d)
    raise ValueError(f"Watchlist id '{wl_id}' tidak ditemukan")


def set_description(wl_id: str, description: str) -> Watchlist:
    data = _load()
    for d in data:
        if d["id"] != wl_id:
            continue
        d["description"] = description
        d["updated_at"] = _now()
        _save(data)
        return _to_model(d)
    raise ValueError(f"Watchlist id '{wl_id}' tidak ditemukan")


def add_tag(wl_id: str, tag: str) -> Watchlist:
    data = _load()
    for d in data:
        if d["id"] != wl_id:
            continue
        tags = d.get("tags", [])
        if tag in tags:
            raise ValueError(f"Tag '{tag}' sudah ada")
        tags.append(tag)
        d["tags"] = tags
        d["updated_at"] = _now()
        _save(data)
        return _to_model(d)
    raise ValueError(f"Watchlist id '{wl_id}' tidak ditemukan")


def remove_tag(wl_id: str, tag: str) -> Watchlist:
    data = _load()
    for d in data:
        if d["id"] != wl_id:
            continue
        tags = d.get("tags", [])
        if tag not in tags:
            raise ValueError(f"Tag '{tag}' tidak ditemukan")
        tags.remove(tag)
        d["tags"] = tags
        d["updated_at"] = _now()
        _save(data)
        return _to_model(d)
    raise ValueError(f"Watchlist id '{wl_id}' tidak ditemukan")


def set_notes(wl_id: str, notes: str) -> Watchlist:
    data = _load()
    for d in data:
        if d["id"] != wl_id:
            continue
        d["notes"] = notes
        d["updated_at"] = _now()
        _save(data)
        return _to_model(d)
    raise ValueError(f"Watchlist id '{wl_id}' tidak ditemukan")


def toggle_favorite(wl_id: str) -> Watchlist:
    data = _load()
    for d in data:
        if d["id"] != wl_id:
            continue
        d["favorite"] = not d.get("favorite", False)
        d["updated_at"] = _now()
        _save(data)
        return _to_model(d)
    raise ValueError(f"Watchlist id '{wl_id}' tidak ditemukan")


def reorder(wl_id: str, tickers: list[str]) -> Watchlist:
    data = _load()
    for d in data:
        if d["id"] != wl_id:
            continue
        existing = {e["ticker"] for e in d["entries"]}
        given = set(tickers)
        if given != existing:
            raise ValueError("Daftar ticker tidak cocok dengan isi watchlist")
        seen: set[str] = set()
        ordered: list[dict] = []
        for t in tickers:
            nt = normalize(t)
            if nt in seen:
                continue
            seen.add(nt)
            entry = next(e for e in d["entries"] if e["ticker"] == nt)
            entry["position"] = len(ordered)
            ordered.append(entry)
        d["entries"] = ordered
        d["updated_at"] = _now()
        _save(data)
        return _to_model(d)
    raise ValueError(f"Watchlist id '{wl_id}' tidak ditemukan")
