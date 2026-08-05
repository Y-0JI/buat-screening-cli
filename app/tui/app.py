from textual.app import App
from textual.binding import Binding

from app.tui.executor import SubprocessExecutor
from app.tui.registry import Feature, FeatureStatus
from app.tui.screens.dashboard import DashboardScreen
from app.tui.screens.planned import PlannedScreen
from app.tui.screens.viewer import CommandViewerScreen


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
            screen = PlannedScreen(feature)
        else:
            screen = CommandViewerScreen(feature, self._executor)
        self.push_screen(screen)

    def action_quit_app(self) -> None:
        self.exit()


def main() -> None:
    ScreeningApp().run()
