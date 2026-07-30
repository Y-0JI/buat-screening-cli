import json
import os
from datetime import datetime, timezone

from app.memory.models import MemoryEntry, MemoryType

_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "ai_memory.json")
_MAX_ENTRIES = 100


class MemoryStore:
    def __init__(self, path: str | None = None) -> None:
        self._path = path or _DATA_PATH

    def add(self, type: MemoryType, content: str, source: str | None = None) -> MemoryEntry:
        entries = self.get_all()
        entry = MemoryEntry(type=type, content=content, source=source)
        entries.append(entry)
        self._enforce_limit(entries)
        self._save(entries)
        return entry

    def get_recent(self, limit: int = 10) -> list[MemoryEntry]:
        entries = self.get_all()
        entries.sort(key=lambda e: e.created_at, reverse=True)
        return entries[:limit]

    def get_by_type(self, type: MemoryType, limit: int = 10) -> list[MemoryEntry]:
        entries = self.get_all()
        filtered = [e for e in entries if e.type == type]
        filtered.sort(key=lambda e: e.created_at, reverse=True)
        return filtered[:limit]

    def get_all(self) -> list[MemoryEntry]:
        if not os.path.exists(self._path):
            return []
        with open(self._path) as f:
            data = json.load(f)
        entries = []
        for e in data.get("entries", []):
            e["type"] = MemoryType(e["type"])
            e["created_at"] = datetime.fromisoformat(e["created_at"])
            e["updated_at"] = datetime.fromisoformat(e["updated_at"])
            entries.append(MemoryEntry(**e))
        return entries

    def forget(self, entry_id: str) -> bool:
        entries = self.get_all()
        new_entries = [e for e in entries if e.id != entry_id]
        if len(new_entries) == len(entries):
            return False
        self._save(new_entries)
        return True

    def clear(self) -> None:
        self._save([])

    def count(self) -> int:
        return len(self.get_all())

    def _enforce_limit(self, entries: list[MemoryEntry]) -> None:
        if len(entries) > _MAX_ENTRIES:
            entries.sort(key=lambda e: e.created_at)
            del entries[: len(entries) - _MAX_ENTRIES]

    def _save(self, entries: list[MemoryEntry]) -> None:
        data = {
            "version": 1,
            "entries": [
                {
                    "id": e.id,
                    "type": e.type.value,
                    "content": e.content,
                    "source": e.source,
                    "created_at": e.created_at.isoformat(),
                    "updated_at": e.updated_at.isoformat(),
                }
                for e in entries
            ],
        }
        with open(self._path, "w") as f:
            json.dump(data, f, indent=2)

    def serialize_for_prompt(self, limit: int = 10) -> str:
        entries = self.get_recent(limit)
        if not entries:
            return ""
        lines = ["[MEMORI DARI SESI SEBELUMNYA]"]
        for e in entries:
            source = f" ({e.source})" if e.source else ""
            lines.append(f"- {e.content}{source}")
        lines.append("[/MEMORI]")
        return "\n".join(lines)
