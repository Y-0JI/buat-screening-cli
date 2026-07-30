from app.services.watchlist import (
    create, rename, delete, list_all, get_by_id,
    add_symbol, remove_symbol, reorder,
    set_description, add_tag, remove_tag, set_notes, toggle_favorite,
    refresh_metadata, refresh_all,
    query_entries, find_symbol, search_watchlists,
    reset_data,
)
from app.models.watchlist import Watchlist


def _clean():
    reset_data()


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


def test_set_description():
    _clean()
    w = create("Test")
    w2 = set_description(w.id, "Saham pilihan saya")
    assert w2.description == "Saham pilihan saya"


def test_set_description_empty():
    _clean()
    w = create("Test")
    w2 = set_description(w.id, "")
    assert w2.description == ""


def test_add_tag():
    _clean()
    w = create("Test")
    w2 = add_tag(w.id, "blue-chip")
    assert "blue-chip" in w2.tags


def test_add_tag_duplicate():
    _clean()
    w = create("Test")
    add_tag(w.id, "blue-chip")
    try:
        add_tag(w.id, "blue-chip")
        assert False, "should raise"
    except ValueError:
        pass


def test_remove_tag():
    _clean()
    w = create("Test")
    add_tag(w.id, "blue-chip")
    add_tag(w.id, "dividen")
    w2 = remove_tag(w.id, "blue-chip")
    assert "blue-chip" not in w2.tags
    assert "dividen" in w2.tags


def test_remove_tag_not_found():
    _clean()
    w = create("Test")
    try:
        remove_tag(w.id, "nonexistent")
        assert False, "should raise"
    except ValueError:
        pass


def test_multiple_tags():
    _clean()
    w = create("Test")
    add_tag(w.id, "a")
    add_tag(w.id, "b")
    add_tag(w.id, "c")
    w2 = get_by_id(w.id)
    assert sorted(w2.tags) == ["a", "b", "c"]


def test_set_notes():
    _clean()
    w = create("Test")
    w2 = set_notes(w.id, "Pantau terus")
    assert w2.notes == "Pantau terus"


def test_set_notes_empty():
    _clean()
    w = create("Test")
    set_notes(w.id, "Catatan")
    w2 = set_notes(w.id, "")
    assert w2.notes == ""


def test_toggle_favorite():
    _clean()
    w = create("Test")
    assert not w.favorite
    w2 = toggle_favorite(w.id)
    assert w2.favorite
    w3 = toggle_favorite(w.id)
    assert not w3.favorite


def test_metadata_independent_from_entries():
    _clean()
    w = create("Test")
    set_description(w.id, "Deskripsi")
    add_tag(w.id, "tag1")
    set_notes(w.id, "Catatan")
    toggle_favorite(w.id)
    add_symbol(w.id, "BBCA")
    w2 = get_by_id(w.id)
    assert w2.description == "Deskripsi"
    assert "tag1" in w2.tags
    assert w2.notes == "Catatan"
    assert w2.favorite
    assert len(w2.entries) == 1


def test_metadata_persistence():
    _clean()
    w = create("Test")
    set_description(w.id, "Persisten")
    add_tag(w.id, "tag-a")
    set_notes(w.id, "Aman")
    toggle_favorite(w.id)
    w2 = get_by_id(w.id)
    assert w2.description == "Persisten"
    assert "tag-a" in w2.tags
    assert w2.notes == "Aman"
    assert w2.favorite


def test_new_watchlist_has_default_metadata():
    _clean()
    w = create("Test")
    assert w.description == ""
    assert w.tags == []
    assert w.notes == ""
    assert not w.favorite


def test_tag_case_sensitive():
    _clean()
    w = create("Test")
    add_tag(w.id, "Blue-Chip")
    w2 = add_tag(w.id, "blue-chip")
    assert len(w2.tags) == 2


def test_symbol_metadata_populated():
    _clean()
    w = create("Test")
    w2 = add_symbol(w.id, "BBCA")
    e = w2.entries[0]
    assert e.ticker == "BBCA"
    assert e.name
    assert "Financial" in e.sector


def test_symbol_metadata_unknown_ticker():
    _clean()
    w = create("Test")
    w2 = add_symbol(w.id, "ZZZZ")
    e = w2.entries[0]
    assert e.ticker == "ZZZZ"
    assert e.name == ""
    assert e.sector == ""


def test_symbol_metadata_persisted():
    _clean()
    w = create("Test")
    add_symbol(w.id, "BBRI")
    w2 = get_by_id(w.id)
    e = w2.entries[0]
    assert e.name
    assert "Financial" in e.sector


def test_symbol_metadata_multiple_symbols():
    _clean()
    w = create("Test")
    add_symbol(w.id, "BBCA")
    add_symbol(w.id, "ADRO")
    add_symbol(w.id, "TLKM")
    w2 = get_by_id(w.id)
    names = {e.ticker: e.name for e in w2.entries}
    assert names["BBCA"]
    assert names["ADRO"]
    assert names["TLKM"]


def test_symbol_metadata_updated_at_add():
    _clean()
    w = create("Test")
    w2 = add_symbol(w.id, "BBCA")
    e = w2.entries[0]
    assert e.added_at
    assert e.position == 0


def test_add_symbol_preserves_existing_entries():
    _clean()
    w = create("Test")
    add_symbol(w.id, "BBCA")
    w2 = add_symbol(w.id, "BBRI")
    assert len(w2.entries) == 2
    assert w2.entries[0].ticker == "BBCA"
    assert w2.entries[1].ticker == "BBRI"


def test_symbol_valid_flag_set():
    _clean()
    w = create("Test")
    w2 = add_symbol(w.id, "BBCA")
    assert w2.entries[0].valid is True


def test_refresh_metadata():
    _clean()
    w = create("Test")
    w2 = add_symbol(w.id, "BBCA")
    assert w2.entries[0].name
    w3 = refresh_metadata(w.id)
    assert w3.entries[0].name
    assert w3.entries[0].last_synced


def test_refresh_metadata_invalid_id():
    _clean()
    try:
        refresh_metadata("nonexistent")
        assert False, "should raise"
    except ValueError:
        pass


def test_refresh_all():
    _clean()
    w1 = create("A")
    w2 = create("B")
    add_symbol(w1.id, "BBCA")
    add_symbol(w2.id, "BBRI")
    results = refresh_all()
    assert len(results) == 3  # default + A + B
    for r in results:
        assert "id" in r
        assert "name" in r


def test_refresh_all_empty_watchlist():
    _clean()
    results = refresh_all()
    assert len(results) == 1  # default watchlist only, no entries


def test_sync_updates_valid_flag():
    _clean()
    w = create("Test")
    add_symbol(w.id, "BBCA")
    w2 = refresh_metadata(w.id)
    assert w2.entries[0].valid is True


def test_query_entries_search_ticker():
    _clean()
    w = create("Test")
    add_symbol(w.id, "BBCA")
    add_symbol(w.id, "BBRI")
    r = query_entries(w.id, search="BBCA")
    assert len(r.entries) == 1
    assert r.entries[0].ticker == "BBCA"


def test_query_entries_search_name():
    _clean()
    w = create("Test")
    add_symbol(w.id, "BBCA")
    r = query_entries(w.id, search="bank")
    assert len(r.entries) >= 1


def test_query_entries_search_no_match():
    _clean()
    w = create("Test")
    add_symbol(w.id, "BBCA")
    r = query_entries(w.id, search="ZZZZZZ")
    assert len(r.entries) == 0


def test_query_entries_filter_sector():
    _clean()
    w = create("Test")
    add_symbol(w.id, "BBCA")
    add_symbol(w.id, "ADRO")
    r = query_entries(w.id, sector="Energy")
    assert all("Energy" in e.sector for e in r.entries)
    assert any(e.ticker == "ADRO" for e in r.entries)


def test_query_entries_filter_valid():
    _clean()
    w = create("Test")
    add_symbol(w.id, "BBCA")
    add_symbol(w.id, "ZZZZ")
    r = query_entries(w.id, valid=True)
    assert all(e.valid for e in r.entries)


def test_query_entries_sort_ticker():
    _clean()
    w = create("Test")
    add_symbol(w.id, "BBRI")
    add_symbol(w.id, "BBCA")
    add_symbol(w.id, "ADRO")
    r = query_entries(w.id, sort_by="ticker")
    tickers = [e.ticker for e in r.entries]
    assert tickers == sorted(tickers)


def test_query_entries_sort_name():
    _clean()
    w = create("Test")
    add_symbol(w.id, "BBCA")
    add_symbol(w.id, "ADRO")
    r = query_entries(w.id, sort_by="name")
    names = [e.name for e in r.entries]
    assert names == sorted(names)


def test_query_entries_combined():
    _clean()
    w = create("Test")
    add_symbol(w.id, "BBCA")
    add_symbol(w.id, "BBRI")
    add_symbol(w.id, "ADRO")
    r = query_entries(w.id, sector="Financials", sort_by="ticker")
    assert all("Financials" in e.sector for e in r.entries)
    tickers = [e.ticker for e in r.entries]
    assert tickers == sorted(tickers)


def test_find_symbol_found():
    _clean()
    w = create("Test")
    add_symbol(w.id, "BBCA")
    add_symbol(w.id, "ADRO")
    results = find_symbol("BBCA")
    assert len(results) >= 1
    assert results[0]["name"] == "Test"


def test_find_symbol_not_found():
    _clean()
    w = create("Test")
    add_symbol(w.id, "BBCA")
    results = find_symbol("ZZZZZZ")
    assert len(results) == 0


def test_search_watchlists_by_name():
    _clean()
    w = create("Portofolio Saya")
    results = search_watchlists(name="portofolio")
    assert any(r.id == w.id for r in results)


def test_search_watchlists_by_tag():
    _clean()
    w = create("Test")
    add_tag(w.id, "blue-chip")
    results = search_watchlists(tag="blue")
    assert any(r.id == w.id for r in results)


def test_search_watchlists_by_favorite():
    _clean()
    w = create("Test")
    toggle_favorite(w.id)
    results = search_watchlists(favorite=True)
    assert any(r.id == w.id for r in results)
