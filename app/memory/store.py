import json
import os
from datetime import datetime, timezone

from loguru import logger
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
        try:
            with open(self._path) as f:
                data = json.load(f)
        except (json.JSONDecodeError, ValueError, KeyError, TypeError) as exc:
            logger.warning(f"Corrupt memory file, starting fresh: {exc}")
            return []
        entries = []
        for e in data.get("entries", []):
            try:
                e["type"] = MemoryType(e["type"])
                e["created_at"] = datetime.fromisoformat(e["created_at"])
                e["updated_at"] = datetime.fromisoformat(e["updated_at"])
                entries.append(MemoryEntry(**e))
            except (ValueError, KeyError, TypeError) as exc:
                logger.warning(f"Skipping corrupt memory entry {e.get('id', '?' )}: {exc}")
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
        os.makedirs(os.path.dirname(self._path), exist_ok=True)
        tmp = self._path + ".tmp"
        with open(tmp, "w") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp, self._path)

    def get_relevant(self, query: str, limit: int = 5) -> list[MemoryEntry]:
        if not query:
            return []
        words = [w.lower() for w in query.split()]
        entries = self.get_all()
        if len(words) == 1:
            matched = [e for e in entries if any(w in e.content.lower() or (e.source and w in e.source.lower()) for w in words)]
        else:
            matched = [e for e in entries if all(w in e.content.lower() or (e.source and w in e.source.lower()) for w in words)]
        matched.sort(key=lambda e: e.created_at, reverse=True)
        return matched[:limit]

    def add_or_update(self, type: MemoryType, content: str, source: str | None = None) -> MemoryEntry:
        entries = self.get_all()
        for e in entries:
            if e.type == type and e.source == source:
                e.content = content
                e.updated_at = datetime.now(timezone.utc)
                self._save(entries)
                return e
        return self.add(type, content, source)

    def serialize_for_prompt(self, ticker: str = "", limit: int = 10) -> str:
        blocks = []

        prefs = self.get_by_type(MemoryType.USER_PREFERENCE)
        if prefs:
            lines = ["[PREFERENSI USER]"]
            for e in prefs:
                lines.append(f"- {e.content}")
            lines.append("[/PREFERENSI USER]")
            blocks.append("\n".join(lines))

        prior = self.get_relevant(ticker, limit=3) if ticker else []
        if prior:
            lines = ["[RISET SEBELUMNYA]"]
            for e in prior:
                lines.append(f"- {e.content}")
            lines.append("[/RISET SEBELUMNYA]")
            blocks.append("\n".join(lines))

        shown_ids = {e.id for e in prefs} | {e.id for e in prior}
        recent = [e for e in self.get_all() if e.id not in shown_ids]
        recent.sort(key=lambda e: e.created_at, reverse=True)
        recent = recent[:limit]
        if recent:
            lines = ["[KONTEKS TERBARU]"]
            for e in recent:
                source = f" ({e.source})" if e.source else ""
                lines.append(f"- {e.content}{source}")
            lines.append("[/KONTEKS TERBARU]")
            blocks.append("\n".join(lines))

        return "\n\n".join(blocks)
