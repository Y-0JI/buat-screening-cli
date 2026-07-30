from app.config.settings import settings

_BACKENDS: dict[str, type] = {}
_test_backend: "StorageBackend | None" = None


def register(name: str, cls: type) -> None:
    _BACKENDS[name] = cls


def set_test_backend(backend: "StorageBackend | None") -> None:
    global _test_backend
    _test_backend = backend


def get_backend() -> "StorageBackend":
    if _test_backend is not None:
        return _test_backend
    name = settings.watchlist_storage
    cls = _BACKENDS.get(name)
    if not cls:
        raise ValueError(f"Storage backend '{name}' tidak dikenal. Tersedia: {list(_BACKENDS)}")
    return cls()


from app.storage.local import LocalJsonStorage  # noqa: E402
from app.storage.sqlite import SqliteStorage  # noqa: E402

register("local", LocalJsonStorage)
register("sqlite", SqliteStorage)
