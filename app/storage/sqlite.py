import json
import os
import sqlite3
from datetime import datetime, timezone

from app.storage.base import StorageBackend

_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "watchlists.db")


class SqliteStorage(StorageBackend):
    def __init__(self) -> None:
        self._conn: sqlite3.Connection | None = None

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(_DB_PATH)
            self._conn.row_factory = sqlite3.Row
            self._init_db()
        return self._conn

    def _init_db(self) -> None:
        conn = self._conn
        conn.executescript(
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
        conn.commit()

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
        if conn:
            conn.rollback()
        return watchlists

    def save(self, data: list[dict]) -> None:
        conn = self._get_conn()
        conn.execute("DELETE FROM entries")
        conn.execute("DELETE FROM watchlists")
        for wl in data:
            tags_json = json.dumps(wl.get("tags", []))
            conn.execute(
                """INSERT INTO watchlists
                (id, name, description, tags, notes, favorite, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    wl["id"], wl["name"], wl.get("description", ""),
                    tags_json, wl.get("notes", ""),
                    int(wl.get("favorite", False)),
                    wl.get("created_at", ""), wl.get("updated_at", ""),
                ),
            )
            for e in wl.get("entries", []):
                conn.execute(
                    """INSERT INTO entries
                    (ticker, name, sector, exchange, industry, currency,
                     valid, last_synced, added_at, position, watchlist_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        e["ticker"], e.get("name", ""), e.get("sector", ""),
                        e.get("exchange", ""), e.get("industry", ""),
                        e.get("currency", ""), int(e.get("valid", True)),
                        e.get("last_synced", ""), e.get("added_at", ""),
                        e.get("position", 0), wl["id"],
                    ),
                )
        conn.commit()
