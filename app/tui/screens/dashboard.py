from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.screen import Screen
from textual.widgets import Footer, Header, Label, ListItem, ListView

from app.tui.registry import FEATURES, GROUPS, Feature, FeatureStatus


class FeatureItem(ListItem):
    def __init__(self, feature: Feature) -> None:
        self.feature = feature
        label = feature.title
        if feature.status == FeatureStatus.PLANNED:
            label += f" [Phase {feature.planned_phase}]"
        super().__init__(Label(label))


class DashboardScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with VerticalScroll():
            for group in GROUPS:
                yield Label(f"[bold]{group}[/]")
                features = [f for f in FEATURES if f.group == group and not f.hidden]
                yield ListView(*[FeatureItem(f) for f in features], id=f"list-{group.lower()}")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#list-analysis", ListView).focus()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        item = event.item
        if isinstance(item, FeatureItem):
            self.app.open_feature(item.feature)
