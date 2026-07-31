from app.storage.local import LocalJsonStorage

_test_backend: "StorageBackend | None" = None


def set_test_backend(backend: "StorageBackend | None") -> None:
    global _test_backend
    _test_backend = backend


def get_backend() -> "StorageBackend":
    if _test_backend is not None:
        return _test_backend
    return LocalJsonStorage()
