from textual.app import App
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Static


class EmptyScreen(Screen):
    def compose(self):
        yield Static("TUI placeholder")


class ScreeningApp(App):
    TITLE = "Screening AI — TUI"
    BINDINGS = [Binding("q", "quit_app", "Keluar")]

    def on_mount(self) -> None:
        self.push_screen(EmptyScreen())

    def action_quit_app(self) -> None:
        self.exit()


def main() -> None:
    ScreeningApp().run()
