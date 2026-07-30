import json
import os

from app.storage.base import StorageBackend

_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "watchlists.json")


class LocalJsonStorage(StorageBackend):
    def load(self) -> list[dict]:
        if not os.path.exists(_DATA_PATH):
            return []
        with open(_DATA_PATH) as f:
            return json.load(f)

    def save(self, data: list[dict]) -> None:
        with open(_DATA_PATH, "w") as f:
            json.dump(data, f, indent=2)
