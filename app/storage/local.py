import json
import os

from app.storage.base import StorageBackend

_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "watchlists.json")


class LocalJsonStorage(StorageBackend):
    def __init__(self, path: str | None = None) -> None:
        self._path = path or _DATA_PATH

    def load(self) -> list[dict]:
        if not os.path.exists(self._path):
            return []
        with open(self._path) as f:
            return json.load(f)

    def save(self, data: list[dict]) -> None:
        with open(self._path, "w") as f:
            json.dump(data, f, indent=2)
