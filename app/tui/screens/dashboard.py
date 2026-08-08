from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.screen import Screen
from textual.widgets import Footer, Header, Input, Label, ListItem, ListView

from app.tui.registry import FEATURES, GROUPS, Feature, FeatureStatus, feature_matches
from app.tui.shortcuts import SHORTCUTS


class FeatureItem(ListItem):
    def __init__(self, feature: Feature) -> None:
        self.feature = feature
        label = feature.title
        if feature.status == FeatureStatus.PLANNED:
            label += f" [Phase {feature.planned_phase}]"
        super().__init__(Label(label))


class DashboardScreen(Screen):
    BINDINGS = [
        Binding("/", "search", "Cari"),
        Binding("?", "help", "Bantuan"),
        Binding("[", "prev_group", "Grup sebelumnya"),
        Binding("]", "next_group", "Grup berikutnya"),
    ] + [Binding(k, f'quick("{key}")', title) for k, (key, title) in SHORTCUTS.items()]

    def __init__(self) -> None:
        super().__init__()
        self._query = ""

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        yield Input(placeholder="Cari fitur... (/)", id="search")
        with VerticalScroll():
            for group in GROUPS:
                yield Label(f"[bold]{group}[/]")
                yield ListView(id=f"list-{group.lower()}")
        yield Footer()

    def on_mount(self) -> None:
        self._apply_filter()
        self.query_one("#list-analysis", ListView).focus()

    def action_search(self) -> None:
        self.query_one("#search", Input).focus()

    def action_help(self) -> None:
        from app.tui.screens.help import HelpScreen
        self.app.push_screen(HelpScreen())

    def action_quick(self, key: str) -> None:
        self.app.open_feature_key(key)

    def action_prev_group(self) -> None:
        self._shift_group(-1)

    def action_next_group(self) -> None:
        self._shift_group(1)

    def _shift_group(self, delta: int) -> None:
        ids = [f"list-{g.lower()}" for g in GROUPS]
        focused = getattr(self.app.focused, "id", None)
        idx = ids.index(focused) if focused in ids else 0
        nxt = (idx + delta) % len(ids)
        self.query_one(f"#{ids[nxt]}", ListView).focus()

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "search":
            self._query = event.value.strip().lower()
            self._apply_filter()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id != "search":
            return
        for group in GROUPS:
            for item in self.query_one(f"#list-{group.lower()}", ListView).children:
                if isinstance(item, FeatureItem) and self._matches(item.feature):
                    self.app.open_feature(item.feature)
                    return

    def on_key(self, event) -> None:
        if event.key == "escape" and self.query_one("#search", Input).has_focus:
            self.query_one("#search", Input).value = ""
            self._query = ""
            self._apply_filter()
            self.query_one("#list-analysis", ListView).focus()
            event.stop()

    def _matches(self, feature: Feature) -> bool:
        return feature_matches(feature, self._query)

    def _apply_filter(self) -> None:
        for group in GROUPS:
            lv = self.query_one(f"#list-{group.lower()}", ListView)
            lv.clear()
            features = [f for f in FEATURES if f.group == group and not f.hidden and self._matches(f)]
            lv.extend(FeatureItem(f) for f in features)
            if lv.children:
                lv.index = 0

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        item = event.item
        if isinstance(item, FeatureItem):
            self.app.open_feature(item.feature)
