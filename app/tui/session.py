"""Riwayat chat TUI antar sesi — file runtime sederhana (JSON list)."""

import json
from pathlib import Path

_PATH = Path(__file__).resolve().parent.parent / "data" / "tui_session.json"
_MAX_LINES = 200


def load_history() -> list[str]:
    try:
        data = json.loads(_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    history = data.get("chat_history")
    return history if isinstance(history, list) else []


def save_history(lines) -> None:
    try:
        _PATH.write_text(json.dumps({"chat_history": list(lines)[-_MAX_LINES:]}, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass