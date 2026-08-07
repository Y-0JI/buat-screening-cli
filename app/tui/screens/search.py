import re

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Footer, Header, Input, Static

from app.tui.registry import FEATURES, exact_feature_match

_COMPOSITE = next(f for f in FEATURES if f.key == "composite")
_TICKER_RE = re.compile(r"^[A-Z]{2,5}$")


class SearchScreen(Screen):
    """Landing: satu input query. f2 → menu klasik (dashboard).

    Aturan disambiguasi submit (urutan prioritas):
      1. exact_feature_match — nama/key/keyword fitur PERSIS → fitur itu
         (menang atas bentuk kode saham: 'trend'/'naik' = fitur, bukan ticker)
      2. token 2-5 huruf kapital (^[A-Z]{2,5}$) → composite langsung
      3. sisanya → ChatScreen natural (CLI natural() yang putuskan intent)
    Substring match TIDAK dipakai di landing — hanya dashboard."""
    BINDINGS = [
        Binding("f2", "open_dashboard", "Menu (f2)"),
        Binding("ctrl+q", "quit_app", "Keluar"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        yield Input(
            placeholder="Ketik ticker, query, atau nama fitur...  (f2: menu)",
            id="search",
        )
        yield Static(
            "[dim]Contoh: BBCA • analisa BBCA • gainers • f2 untuk menu fitur[/dim]",
            id="hint",
        )
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#search", Input).focus()

    def action_open_dashboard(self) -> None:
        self.app.open_dashboard()

    def on_key(self, event) -> None:
        if event.key == "escape" and self.query_one("#search", Input).has_focus:
            inp = self.query_one("#search", Input)
            inp.value = ""
            inp.focus()
            event.stop()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id != "search":
            return
        q = event.value.strip()
        if not q:
            return
        feature = exact_feature_match(q)
        if feature is not None:
            self.app.open_feature(feature)
            return
        if _TICKER_RE.match(q.upper()):
            self.app.open_feature_direct(_COMPOSITE, {"ticker": q.upper()})
            return
        self.app.open_natural(q)
