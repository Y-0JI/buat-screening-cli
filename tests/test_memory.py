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
    assert "[KONTEKS TERBARU]" in text
    assert "BBCA: bagus" in text
    assert "[/KONTEKS TERBARU]" in text


def test_serialize_with_preferences():
    store = MemoryStore(path="/tmp/test_memory.json")
    store.clear()
    store.add(MemoryType.USER_PREFERENCE, "Bahasa Indonesia", source="user")
    store.add(MemoryType.RESEARCH_FINDING, "BBCA: laba naik", source="BBCA")
    text = store.serialize_for_prompt(ticker="BBCA")
    assert "[PREFERENSI USER]" in text
    assert "[RISET SEBELUMNYA]" in text
    assert "BBCA: laba naik" in text
    assert "Bahasa Indonesia" in text


def test_get_relevant():
    store = MemoryStore(path="/tmp/test_memory.json")
    store.clear()
    store.add(MemoryType.RESEARCH_FINDING, "BBCA: laba naik 15%", source="BBCA")
    store.add(MemoryType.RESEARCH_FINDING, "BBRI: valuasi murah", source="BBRI")
    r = store.get_relevant("BBCA")
    assert len(r) == 1
    assert "BBCA" in r[0].content


def test_get_relevant_no_match():
    store = MemoryStore(path="/tmp/test_memory.json")
    store.clear()
    store.add(MemoryType.RESEARCH_FINDING, "BBCA: laba naik", source="BBCA")
    r = store.get_relevant("TIDAKADA")
    assert r == []


def test_get_relevant_multi_word_tight():
    store = MemoryStore(path="/tmp/test_memory.json")
    store.clear()
    store.add(MemoryType.RESEARCH_FINDING, "BBCA: laba naik 15%", source="BBCA")
    store.add(MemoryType.RESEARCH_FINDING, "saham bank bagus", source="BANK")
    r = store.get_relevant("saham bank")
    assert len(r) == 1
    assert r[0].source == "BANK"


def test_get_relevant_multi_word_mixed_fields():
    store = MemoryStore(path="/tmp/test_memory.json")
    store.clear()
    store.add(MemoryType.RESEARCH_FINDING, "BBCA: laba naik 15%", source="BBCA")
    store.add(MemoryType.RESEARCH_FINDING, "saham bank bagus", source="BANK")
    r = store.get_relevant("BBCA laba")
    assert len(r) == 1
    assert r[0].source == "BBCA"


def test_get_relevant_multi_word_duplicate_content():
    store = MemoryStore(path="/tmp/test_memory.json")
    store.clear()
    store.add(MemoryType.RESEARCH_FINDING, "BBCA: laba naik 15%", source="BBCA")
    store.add(MemoryType.RESEARCH_FINDING, "BBCA: laba turun 5%", source="BBCA")
    r = store.get_relevant("BBCA laba")
    assert len(r) == 2


def test_get_relevant_multi_word_unknown_ticker():
    store = MemoryStore(path="/tmp/test_memory.json")
    store.clear()
    store.add(MemoryType.RESEARCH_FINDING, "BBCA: laba naik 15%", source="BBCA")
    r = store.get_relevant("XYZB laba")
    assert r == []


def test_add_or_update_updates_existing():
    store = MemoryStore(path="/tmp/test_memory.json")
    store.clear()
    e1 = store.add_or_update(MemoryType.RESEARCH_FINDING, "BBCA: lama", source="BBCA")
    e2 = store.add_or_update(MemoryType.RESEARCH_FINDING, "BBCA: baru", source="BBCA")
    assert e1.id == e2.id
    assert e2.content == "BBCA: baru"
    assert store.count() == 1


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


def test_corrupt_file():
    path = "/tmp/test_memory_corrupt.json"
    with open(path, "w") as f:
        f.write("{invalid json}}")
    store = MemoryStore(path=path)
    assert store.get_all() == []
    assert store.count() == 0


def test_fresh_installation():
    path = "/tmp/test_fresh/memory.json"
    store = MemoryStore(path=path)
    store.add(MemoryType.RESEARCH_FINDING, "test")
    assert store.count() == 1
    import shutil
    shutil.rmtree("/tmp/test_fresh", ignore_errors=True)


def test_atomic_write_resilience():
    path = "/tmp/test_atomic_memory.json"
    store = MemoryStore(path=path)
    store.clear()
    store.add(MemoryType.RESEARCH_FINDING, "entry1")
    assert os.path.exists(path)
    store.add(MemoryType.RESEARCH_FINDING, "entry2")
    assert store.count() == 2
