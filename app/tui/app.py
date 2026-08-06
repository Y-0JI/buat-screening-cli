from textual.app import App
from textual.binding import Binding

from app.tui.executor import SubprocessExecutor
from app.tui.registry import FEATURES, Feature, FeatureStatus, build_command
from app.tui.screens.chat import ChatScreen
from app.tui.screens.dashboard import DashboardScreen
from app.tui.screens.input import InputFormScreen
from app.tui.screens.planned import PlannedScreen
from app.tui.screens.viewer import CommandViewerScreen
from app.tui.screens.watchlist import WatchlistScreen


class ScreeningApp(App):
    TITLE = "Screening AI — TUI"
    BINDINGS = [Binding("q", "quit_app", "Keluar")]

    def __init__(self) -> None:
        super().__init__()
        self._executor = SubprocessExecutor()

    def on_mount(self) -> None:
        self.push_screen(DashboardScreen())

    def open_feature(self, feature: Feature, initial: dict[str, str] | None = None) -> None:
        if feature.status == FeatureStatus.PLANNED:
            screen = PlannedScreen(feature)
        elif feature.workspace == "chat":
            screen = ChatScreen(feature, self._executor)
        elif feature.workspace == "watchlist":
            screen = WatchlistScreen()
        elif any(arg.required for arg in feature.args):
            screen = InputFormScreen(feature, initial)
        else:
            screen = CommandViewerScreen(feature, feature.command, self._executor)
        self.push_screen(screen)

    def submit_feature(self, feature: Feature, values: dict[str, str]) -> None:
        argv = build_command(feature, values)
        self.pop_screen()
        self.push_screen(CommandViewerScreen(feature, argv, self._executor))

    def open_feature_direct(self, feature: Feature, values: dict[str, str]) -> None:
        argv = build_command(feature, values)
        self.push_screen(CommandViewerScreen(feature, argv, self._executor))

    def open_feature_key(self, key: str) -> None:
        feature = next(f for f in FEATURES if f.key == key)
        self.open_feature(feature)

    def action_quit_app(self) -> None:
        self.exit()


def main() -> None:
    ScreeningApp().run()
