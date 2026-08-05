from textual.app import App
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Static

from app.tui.executor import SubprocessExecutor
from app.tui.registry import Feature, FeatureStatus
from app.tui.screens.dashboard import DashboardScreen
from app.tui.screens.viewer import CommandViewerScreen


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

    def __init__(self) -> None:
        super().__init__()
        self._executor = SubprocessExecutor()

    def on_mount(self) -> None:
        self.push_screen(DashboardScreen())

    def open_feature(self, feature: Feature) -> None:
        if feature.status == FeatureStatus.PLANNED:
            screen = _FeatureNote(feature, "Tersedia di Phase 2")
        else:
            screen = CommandViewerScreen(feature, self._executor)
        self.push_screen(screen)

    def action_quit_app(self) -> None:
        self.exit()


def main() -> None:
    ScreeningApp().run()
