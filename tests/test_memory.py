import os
import tempfile

from app.memory import get_store
from app.memory.models import MemoryType, MemoryEntry
from app.memory.store import MemoryStore


def test_add_and_recent():
    store = MemoryStore(path="/tmp/test_memory.json")
    store.clear()
    e = store.add(MemoryType.RESEARCH_FINDING, "BBCA: laba naik 15%", source="BBCA")
    assert e.id
    assert e.type == MemoryType.RESEARCH_FINDING
    recent = store.get_recent(5)
    assert len(recent) == 1
    assert recent[0].content == "BBCA: laba naik 15%"


def test_get_by_type():
    store = MemoryStore(path="/tmp/test_memory.json")
    store.clear()
    store.add(MemoryType.USER_PREFERENCE, "Bahasa Indonesia", source="user")
    store.add(MemoryType.RESEARCH_FINDING, "BBRI: valuasi murah", source="BBRI")
    pref = store.get_by_type(MemoryType.USER_PREFERENCE)
    assert len(pref) == 1
    assert pref[0].content == "Bahasa Indonesia"


def test_forget():
    store = MemoryStore(path="/tmp/test_memory.json")
    store.clear()
    e = store.add(MemoryType.IMPORTANT_CONTEXT, "User suka saham dividen")
    assert store.forget(e.id) is True
    assert store.count() == 0
    assert store.forget("nonexistent") is False


def test_clear():
    store = MemoryStore(path="/tmp/test_memory.json")
    store.clear()
    store.add(MemoryType.RESEARCH_FINDING, "test")
    assert store.count() == 1
    store.clear()
    assert store.count() == 0


def test_auto_cleanup():
    store = MemoryStore(path="/tmp/test_memory.json")
    store.clear()
    for i in range(105):
        store.add(MemoryType.RESEARCH_FINDING, f"entry {i}")
    assert store.count() <= 100


def test_serialize_for_prompt():
    store = MemoryStore(path="/tmp/test_memory.json")
    store.clear()
    store.add(MemoryType.RESEARCH_FINDING, "BBCA: bagus", source="BBCA")
    text = store.serialize_for_prompt()
    assert "[MEMORI DARI SESI SEBELUMNYA]" in text
    assert "BBCA: bagus" in text
    assert "[/MEMORI]" in text


def test_persistence():
    path = "/tmp/test_memory_persist.json"
    store = MemoryStore(path=path)
    store.clear()
    store.add(MemoryType.USER_PREFERENCE, "mode gelap")
    store2 = MemoryStore(path=path)
    assert store2.count() == 1
    assert store2.get_recent()[0].content == "mode gelap"


def test_serialize_empty():
    store = MemoryStore(path="/tmp/test_memory_empty.json")
    store.clear()
    assert store.serialize_for_prompt() == ""
