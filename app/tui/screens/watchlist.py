from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Footer, Label, ListItem, ListView

from app.services.watchlist import list_all
from app.tui.registry import FEATURES

# Pengecualian eksplisit: daftar watchlist dibaca in-process (read-only),
# karena output CLI `watchlist list` berupa tabel rich (tidak machine-readable)
# dan data bersifat lokal. Mutasi tetap via Executor (CLI) — bukan pola umum.


class _WatchlistItem(ListItem):
    def __init__(self, name: str, label: str) -> None:
        self.wl_name = name
        super().__init__(Label(label))


class WatchlistScreen(Screen):
    BINDINGS = [
        Binding("a", "add", "Tambah Simbol"),
        Binding("r", "remove", "Hapus Simbol"),
        Binding("n", "create", "Buat Baru"),
        Binding("d", "delete", "Hapus"),
        Binding("escape", "back", "Kembali"),
        Binding("b", "back", "Kembali"),
    ]

    def compose(self) -> ComposeResult:
        yield Label("[bold]Watchlist[/bold]")
        yield ListView(id="wl-list")
        yield Footer()

    def on_mount(self) -> None:
        self.refresh_data()

    def on_screen_resume(self, event) -> None:
        self.refresh_data()

    def refresh_data(self) -> None:
        lv = self.query_one("#wl-list", ListView)
        lv.clear()
        watchlists = list_all()
        if not watchlists:
            lv.append(_WatchlistItem("Belum ada watchlist", "Belum ada watchlist"))
        for w in watchlists:
            fav = " ★" if w.favorite else ""
            lv.append(_WatchlistItem(w.name, f"{w.name} ({len(w.entries)}){fav}"))
        lv.focus()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        item = event.item
        if isinstance(item, _WatchlistItem) and item.wl_name != "Belum ada watchlist":
            feature = next(f for f in FEATURES if f.key == "watchlist-show")
            self.app.open_feature_direct(feature, {"wl_id": item.wl_name})

    def _selected_name(self) -> str | None:
        lv = self.query_one("#wl-list", ListView)
        item = lv.highlighted_child
        if isinstance(item, _WatchlistItem):
            return item.wl_name
        return None

    def open_watchlist(self) -> None:
        name = self._selected_name()
        if not name:
            return
        feature = next(f for f in FEATURES if f.key == "watchlist-show")
        self.app.open_feature_direct(feature, {"wl_id": name})

    def action_add(self) -> None:
        self.app.open_feature_key("watchlist-add")

    def action_remove(self) -> None:
        self.app.open_feature_key("watchlist-remove")

    def action_create(self) -> None:
        self.app.open_feature_key("watchlist-create")

    def action_delete(self) -> None:
        self.app.open_feature_key("watchlist-delete")

    def action_back(self) -> None:
        self.app.pop_screen()