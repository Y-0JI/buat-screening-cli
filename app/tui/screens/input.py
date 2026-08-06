from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Footer, Input, Label, Static

from app.tui.registry import Feature


class InputFormScreen(Screen):
    BINDINGS = [
        Binding("escape", "back", "Kembali"),
        Binding("b", "back", "Kembali"),
    ]

    def __init__(self, feature: Feature) -> None:
        super().__init__()
        self._feature = feature

    def _required_args(self):
        return [a for a in self._feature.args if a.required]

    def compose(self) -> ComposeResult:
        yield Static(f"[bold]{self._feature.title}[/] — {self._feature.description}")
        with Vertical():
            for arg in self._required_args():
                yield Label(arg.placeholder)
                yield Input(placeholder=arg.placeholder, id=f"input-{arg.name}")
        yield Static("", id="error")
        yield Footer()

    def on_mount(self) -> None:
        args = self._required_args()
        if args:
            self.query_one(f"#input-{args[0].name}", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.action_submit()

    def action_submit(self) -> None:
        values = {}
        for arg in self._required_args():
            inp = self.query_one(f"#input-{arg.name}", Input)
            values[arg.name] = inp.value.strip()
        if any(not v for v in values.values()):
            self.query_one("#error", Static).update("[red]Semua field wajib diisi[/red]")
            return
        self.app.submit_feature(self._feature, values)

    def action_back(self) -> None:
        self.app.pop_screen()
