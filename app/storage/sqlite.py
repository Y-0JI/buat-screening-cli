import json
import os
import sqlite3

from app.storage.base import StorageBackend

_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "watchlists.db")


class SqliteStorage(StorageBackend):
    def __init__(self, path: str | None = None) -> None:
        self._path = path or _DB_PATH
        self._conn: sqlite3.Connection | None = None

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self._path)
            self._conn.row_factory = sqlite3.Row
            self._init_db()
        return self._conn

    def _init_db(self) -> None:
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS watchlists (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                tags TEXT DEFAULT '[]',
                notes TEXT DEFAULT '',
                favorite INTEGER DEFAULT 0,
                created_at TEXT DEFAULT '',
                updated_at TEXT DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS entries (
                ticker TEXT NOT NULL,
                name TEXT DEFAULT '',
                sector TEXT DEFAULT '',
                exchange TEXT DEFAULT '',
                industry TEXT DEFAULT '',
                currency TEXT DEFAULT '',
                market TEXT DEFAULT '',
                valid INTEGER DEFAULT 1,
                last_synced TEXT DEFAULT '',
                added_at TEXT DEFAULT '',
                position INTEGER DEFAULT 0,
                watchlist_id TEXT NOT NULL,
                PRIMARY KEY (ticker, watchlist_id),
                FOREIGN KEY (watchlist_id) REFERENCES watchlists(id)
            );
            """
        )
        self._conn.commit()

    def load(self) -> list[dict]:
        conn = self._get_conn()
        cur = conn.execute("SELECT * FROM watchlists ORDER BY created_at")
        watchlists = []
        for row in cur.fetchall():
            wl = dict(row)
            wl["tags"] = json.loads(wl["tags"])
            wl["favorite"] = bool(wl["favorite"])
            entries = conn.execute(
                "SELECT * FROM entries WHERE watchlist_id = ? ORDER BY position", (wl["id"],)
            ).fetchall()
            wl["entries"] = []
            for e in entries:
                entry = dict(e)
                entry["valid"] = bool(entry["valid"])
                wl["entries"].append(entry)
            watchlists.append(wl)
        conn.rollback()
        return watchlists

    def _save_watchlist(self, conn: sqlite3.Connection, wl: dict) -> None:
        tags_json = json.dumps(wl.get("tags", []))
        conn.execute(
            """INSERT OR REPLACE INTO watchlists
            (id, name, description, tags, notes, favorite, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                wl["id"], wl["name"], wl.get("description", ""),
                tags_json, wl.get("notes", ""),
                int(wl.get("favorite", False)),
                wl.get("created_at", ""), wl.get("updated_at", ""),
            ),
        )

    def _save_entry(self, conn: sqlite3.Connection, entry: dict, wl_id: str) -> None:
        conn.execute(
            """INSERT OR REPLACE INTO entries
            (ticker, name, sector, exchange, industry, currency, market,
             valid, last_synced, added_at, position, watchlist_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                entry["ticker"], entry.get("name", ""), entry.get("sector", ""),
                entry.get("exchange", ""), entry.get("industry", ""),
                entry.get("currency", ""), entry.get("market", ""),
                int(entry.get("valid", True)),
                entry.get("last_synced", ""), entry.get("added_at", ""),
                entry.get("position", 0), wl_id,
            ),
        )

    def save_full(self, data: list[dict]) -> None:
        conn = self._get_conn()
        conn.execute("DELETE FROM entries")
        conn.execute("DELETE FROM watchlists")
        for wl in data:
            self._save_watchlist(conn, wl)
            for e in wl.get("entries", []):
                self._save_entry(conn, e, wl["id"])
        conn.commit()

    def save(self, data: list[dict]) -> None:
        conn = self._get_conn()
        existing = self.load()
        existing_by_id = {wl["id"]: wl for wl in existing}
        new_ids = {wl["id"] for wl in data}

        def _key(wl):
            return json.dumps(wl, sort_keys=True, default=str)

        for wl in data:
            old = existing_by_id.get(wl["id"])
            if old is not None and _key(old) == _key(wl):
                continue
            self._save_watchlist(conn, wl)
            conn.execute("DELETE FROM entries WHERE watchlist_id = ?", (wl["id"],))
            for e in wl.get("entries", []):
                self._save_entry(conn, e, wl["id"])

        unused_ids = set(existing_by_id) - new_ids
        for uid in unused_ids:
            conn.execute("DELETE FROM entries WHERE watchlist_id = ?", (uid,))
            conn.execute("DELETE FROM watchlists WHERE id = ?", (uid,))
        conn.commit()
