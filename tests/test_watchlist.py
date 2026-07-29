import json
import os
from app.services.watchlist import _DATA_PATH, create, rename, delete, list_all, get_by_id, add_symbol, remove_symbol, reorder
from app.models.watchlist import Watchlist


def _clean():
    if os.path.exists(_DATA_PATH):
        os.remove(_DATA_PATH)


def test_create():
    _clean()
    w = create("Test")
    assert w.name == "Test"
    assert w.id


def test_create_duplicate_name():
    _clean()
    create("Test")
    try:
        create("Test")
        assert False, "should raise"
    except ValueError:
        pass


def test_rename():
    _clean()
    w = create("A")
    renamed = rename(w.id, "B")
    assert renamed.name == "B"


def test_rename_to_existing():
    _clean()
    create("A")
    w2 = create("B")
    try:
        rename(w2.id, "A")
        assert False, "should raise"
    except ValueError:
        pass


def test_delete():
    _clean()
    w = create("X")
    delete(w.id)
    assert len(list_all()) == 1  # default watchlist remains
    assert list_all()[0].name == "Watchlist Saya"


def test_delete_not_found():
    _clean()
    try:
        delete("nonexistent")
        assert False, "should raise"
    except ValueError:
        pass


def test_list_all():
    _clean()
    assert len(list_all()) == 1  # default
    create("A")
    create("B")
    assert len(list_all()) == 3


def test_get_by_id():
    _clean()
    w = create("Test")
    same = get_by_id(w.id)
    assert same.id == w.id
    assert same.name == w.name


def test_get_by_id_not_found():
    _clean()
    try:
        get_by_id("nonexistent")
        assert False, "should raise"
    except ValueError:
        pass


def test_add_symbol():
    _clean()
    w = create("Test")
    w2 = add_symbol(w.id, "bbca")
    assert len(w2.entries) == 1
    assert w2.entries[0].ticker == "BBCA"


def test_add_duplicate_symbol():
    _clean()
    w = create("Test")
    add_symbol(w.id, "BBCA")
    try:
        add_symbol(w.id, "bbca")
        assert False, "should raise"
    except ValueError:
        pass


def test_add_symbol_different_watchlist():
    _clean()
    w1 = create("A")
    w2 = create("B")
    add_symbol(w1.id, "BBCA")
    add_symbol(w2.id, "BBCA")
    assert len(get_by_id(w1.id).entries) == 1
    assert len(get_by_id(w2.id).entries) == 1


def test_remove_symbol():
    _clean()
    w = create("Test")
    add_symbol(w.id, "BBCA")
    add_symbol(w.id, "BBRI")
    w2 = remove_symbol(w.id, "BBCA")
    assert len(w2.entries) == 1
    assert w2.entries[0].ticker == "BBRI"


def test_remove_not_found():
    _clean()
    w = create("Test")
    try:
        remove_symbol(w.id, "NONEXISTENT")
        assert False, "should raise"
    except ValueError:
        pass


def test_reorder():
    _clean()
    w = create("Test")
    add_symbol(w.id, "BBCA")
    add_symbol(w.id, "BBRI")
    add_symbol(w.id, "BMRI")
    w2 = reorder(w.id, ["BMRI", "BBCA", "BBRI"])
    assert [e.ticker for e in w2.entries] == ["BMRI", "BBCA", "BBRI"]


def test_reorder_mismatch():
    _clean()
    w = create("Test")
    add_symbol(w.id, "BBCA")
    add_symbol(w.id, "BBRI")
    try:
        reorder(w.id, ["BBCA"])
        assert False, "should raise"
    except ValueError:
        pass


def test_persistence():
    _clean()
    create("A")
    w = list_all()[0]
    assert w.name == "Watchlist Saya"
    # reload from file
    list_all()
    list_all()
    assert len(list_all()) == 2


def test_default_watchlist_created():
    _clean()
    watchlists = list_all()
    assert len(watchlists) >= 1
    assert watchlists[0].name == "Watchlist Saya"
