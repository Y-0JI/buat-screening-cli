import json
import os
from datetime import datetime, timezone

from app.models.watchlist import Watchlist, WatchlistEntry
from app.storage import get_backend
from app.validation import normalize

_STOCKS_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "idx_stocks.json")


def _stock_metadata(ticker: str) -> dict:
    t = normalize(ticker)
    try:
        with open(_STOCKS_PATH) as f:
            stocks = json.load(f)
        for s in stocks:
            if s["ticker"] == t:
                return {"name": s.get("name", ""), "sector": s.get("sector", ""), "valid": s.get("valid", True)}
    except Exception:
        pass
    return {"name": "", "sector": "", "valid": True}


def _load() -> list[dict]:
    return get_backend().load()


def _save(data: list[dict]) -> None:
    get_backend().save(data)


def reset_data() -> None:
    _save([])


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
    data = _ensure_default(data)
    for d in data:
        if d["id"] != wl_id and d["name"] == new_name:
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
    data = _ensure_default(data)
    for d in data:
        if d["id"] == wl_id:
            return _to_model(d)
    raise ValueError(f"Watchlist id '{wl_id}' tidak ditemukan")


def add_symbol(wl_id: str, ticker: str) -> Watchlist:
    t = normalize(ticker)
    data = _load()
    data = _ensure_default(data)
    for d in data:
        if d["id"] != wl_id:
            continue
        existing = {e["ticker"] for e in d["entries"]}
        if t in existing:
            raise ValueError(f"'{t}' sudah ada di watchlist")
        meta = _stock_metadata(t)
        pos = len(d["entries"])
        entry = WatchlistEntry(ticker=t, name=meta["name"], sector=meta["sector"], added_at=_now(), position=pos)
        d["entries"].append(entry.model_dump())
        d["updated_at"] = _now()
        _save(data)
        return _to_model(d)
    raise ValueError(f"Watchlist id '{wl_id}' tidak ditemukan")


def remove_symbol(wl_id: str, ticker: str) -> Watchlist:
    t = normalize(ticker)
    data = _load()
    data = _ensure_default(data)
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
    data = _ensure_default(data)
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
    data = _ensure_default(data)
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
    data = _ensure_default(data)
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
    data = _ensure_default(data)
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
    data = _ensure_default(data)
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
    data = _ensure_default(data)
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


_SORT_FIELDS = {"ticker", "name", "sector", "added_at", "position"}


def query_entries(
    wl_id: str,
    search: str = "",
    sector: str = "",
    valid: bool | None = None,
    sort_by: str = "",
    sort_reverse: bool = False,
) -> Watchlist:
    data = _load()
    data = _ensure_default(data)
    for d in data:
        if d["id"] != wl_id:
            continue
        entries = [WatchlistEntry(**e) for e in d["entries"]]
        if search:
            q = search.lower()
            entries = [e for e in entries if q in e.ticker.lower() or q in e.name.lower()]
        if sector:
            s = sector.lower()
            entries = [e for e in entries if s in e.sector.lower()]
        if valid is not None:
            entries = [e for e in entries if e.valid == valid]
        if sort_by in _SORT_FIELDS:
            reverse = sort_reverse
            if sort_by == "position":
                reverse = False
                entries.sort(key=lambda e: e.position or 0, reverse=reverse)
            else:
                entries.sort(key=lambda e, f=sort_by: (getattr(e, f) or "").lower(), reverse=reverse)
        w = _to_model(d)
        w.entries = entries
        return w
    raise ValueError(f"Watchlist id '{wl_id}' tidak ditemukan")


def find_symbol(query: str) -> list[dict]:
    q = query.lower()
    data = _load()
    data = _ensure_default(data)
    results = []
    for d in data:
        matches = [e for e in d.get("entries", []) if q in e["ticker"].lower() or q in e.get("name", "").lower()]
        if matches:
            results.append({"id": d["id"], "name": d["name"], "entries": [WatchlistEntry(**e) for e in matches]})
    return results


def search_watchlists(name: str = "", tag: str = "", favorite: bool | None = None) -> list[Watchlist]:
    data = _load()
    data = _ensure_default(data)
    result = [_to_model(d) for d in data]
    if name:
        n = name.lower()
        result = [w for w in result if n in w.name.lower()]
    if tag:
        t = tag.lower()
        result = [w for w in result if any(t in tg.lower() for tg in w.tags)]
    if favorite is not None:
        result = [w for w in result if w.favorite == favorite]
    return result


def _load_stocks_index() -> dict[str, dict]:
    try:
        with open(_STOCKS_PATH) as f:
            stocks = json.load(f)
        return {s["ticker"]: s for s in stocks}
    except Exception:
        return {}


def _fetch_live_metadata(ticker: str) -> dict | None:
    try:
        from app.tools import get_provider
        provider = get_provider()
        data = provider.fetch(ticker, period="1mo")
        if data and data.info:
            info = data.info
            return {
                "name": info.name or "",
                "sector": info.sector or "",
                "industry": info.industry or "",
                "exchange": info.exchange or "",
                "currency": info.currency or "",
                "market": info.market or "",
                "valid": True,
            }
    except Exception:
        pass
    return None


def _sync_entry(entry: dict, stock_index: dict[str, dict], live: bool = True) -> bool:
    t = entry["ticker"]
    changed = False
    if live:
        live_meta = _fetch_live_metadata(t)
        if live_meta is not None:
            for field in ("name", "sector", "industry", "exchange", "currency", "market"):
                new_val = live_meta.get(field, "")
                if entry.get(field) != new_val:
                    entry[field] = new_val
                    changed = True
            if entry.get("valid") is not True:
                entry["valid"] = True
                changed = True
            entry["last_synced"] = _now()
            return changed
        else:
            if entry.get("valid") is not False:
                entry["valid"] = False
                changed = True
            entry["last_synced"] = _now()
            return changed
    meta = stock_index.get(t)
    if meta:
        for field in ("name", "sector"):
            new_val = meta.get(field, "")
            if entry.get(field) != new_val:
                entry[field] = new_val
                changed = True
        new_valid = meta.get("valid", True)
        if entry.get("valid") != new_valid:
            entry["valid"] = new_valid
            changed = True
    else:
        if entry.get("valid") is not False:
            entry["valid"] = False
            changed = True
    entry["last_synced"] = _now()
    return changed


def refresh_metadata(wl_id: str, live: bool = True) -> Watchlist:
    data = _load()
    stock_index = _load_stocks_index()
    for d in data:
        if d["id"] != wl_id:
            continue
        changed = 0
        for e in d["entries"]:
            if _sync_entry(e, stock_index, live=live):
                changed += 1
        d["updated_at"] = _now()
        _save(data)
        return _to_model(d)
    raise ValueError(f"Watchlist id '{wl_id}' tidak ditemukan")


def refresh_all(live: bool = True) -> list[dict]:
    data = _load()
    data = _ensure_default(data)
    stock_index = _load_stocks_index()
    results = []
    for d in data:
        changed = 0
        for e in d["entries"]:
            if _sync_entry(e, stock_index, live=live):
                changed += 1
        d["updated_at"] = _now()
        results.append({"id": d["id"], "name": d["name"], "changed": changed})
    _save(data)
    return results


def resolve_id(id_or_name: str) -> str:
    data = _load()
    resolved = next((d["id"] for d in data if id_or_name in (d["id"], d["name"])), None)
    if resolved is None:
        raise ValueError(f"Watchlist '{id_or_name}' tidak ditemukan")
    return resolved
