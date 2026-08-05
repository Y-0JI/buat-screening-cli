from textual.app import App
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Static

from app.tui.registry import Feature, FeatureStatus
from app.tui.screens.dashboard import DashboardScreen


class _FeatureNote(Screen):
    def __init__(self, feature: Feature, message: str) -> None:
        super().__init__()
        self._feature = feature
        self._message = message

    def compose(self):
        yield Static(f"[bold]{self._feature.title}[/]\n\n{self._message}\n\n[dim]esc: kembali[/dim]")


class ScreeningApp(App):
    TITLE = "Screening AI — TUI"
    BINDINGS = [Binding("q", "quit_app", "Keluar")]

    def on_mount(self) -> None:
        self.push_screen(DashboardScreen())

    def open_feature(self, feature: Feature) -> None:
        if feature.status == FeatureStatus.PLANNED:
            screen = _FeatureNote(feature, "Tersedia di Phase 2")
        else:
            screen = _FeatureNote(feature, "Eksekusi fitur — dibangun Task 3")
        self.push_screen(screen)

    def action_quit_app(self) -> None:
        self.exit()


def main() -> None:
    ScreeningApp().run()
