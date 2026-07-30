import os
import tempfile

from app.storage.base import StorageBackend
from app.storage.local import LocalJsonStorage
from app.storage.sqlite import SqliteStorage


def _sample_data() -> list[dict]:
    return [
        {
            "id": "wl1",
            "name": "Test",
            "description": "Desc",
            "tags": ["blue-chip"],
            "notes": "Notes",
            "favorite": True,
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
            "entries": [
                {
                    "ticker": "BBCA",
                    "name": "Bank Central Asia",
                    "sector": "Financials",
                    "exchange": "IDX",
                    "industry": "Banking",
                    "currency": "IDR",
                    "valid": True,
                    "last_synced": "2024-01-01T00:00:00",
                    "added_at": "2024-01-01T00:00:00",
                    "position": 0,
                }
            ],
        },
        {
            "id": "wl2",
            "name": "Kosong",
            "description": "",
            "tags": [],
            "notes": "",
            "favorite": False,
            "created_at": "2024-01-02T00:00:00",
            "updated_at": "2024-01-02T00:00:00",
            "entries": [],
        },
    ]


def _test_backend(backend: StorageBackend):
    data = _sample_data()
    backend.save(data)
    loaded = backend.load()
    assert len(loaded) == 2
    assert loaded[0]["id"] == "wl1"
    assert loaded[0]["name"] == "Test"
    assert loaded[0]["tags"] == ["blue-chip"]
    assert loaded[0]["favorite"] is True
    assert len(loaded[0]["entries"]) == 1
    assert loaded[0]["entries"][0]["ticker"] == "BBCA"
    assert loaded[0]["entries"][0]["valid"] is True
    assert loaded[1]["id"] == "wl2"
    assert len(loaded[1]["entries"]) == 0
    assert loaded[1]["favorite"] is False

    backend.save([])
    loaded = backend.load()
    assert loaded == []


def test_local_json():
    backend = LocalJsonStorage()
    _test_backend(backend)


def test_sqlite():
    backend = SqliteStorage()
    _test_backend(backend)
    db_path = backend._get_conn().execute("PRAGMA database_list").fetchone()[2]
    backend._conn.close()
    os.unlink(db_path)


def test_both_backends_produce_same_result():
    wl = _sample_data()
    json_backend = LocalJsonStorage()
    sql_backend = SqliteStorage()
    for backend in (json_backend, sql_backend):
        backend.save(wl)
        loaded = backend.load()
        assert len(loaded) == 2
        assert loaded[0]["entries"][0]["ticker"] == "BBCA"
        assert loaded[1]["entries"] == []
    json_backend.save([])
    sql_backend.save([])
    db_path = sql_backend._get_conn().execute("PRAGMA database_list").fetchone()[2]
    sql_backend._conn.close()
    os.unlink(db_path)
