from app.config.settings import settings

_BACKENDS: dict[str, type] = {}


def register(name: str, cls: type) -> None:
    _BACKENDS[name] = cls


def get_backend() -> "StorageBackend":
    name = settings.watchlist_storage
    cls = _BACKENDS.get(name)
    if not cls:
        raise ValueError(f"Storage backend '{name}' tidak dikenal. Tersedia: {list(_BACKENDS)}")
    return cls()


from app.storage.local import LocalJsonStorage  # noqa: E402
from app.storage.sqlite import SqliteStorage  # noqa: E402

register("local", LocalJsonStorage)
register("sqlite", SqliteStorage)
