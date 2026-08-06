from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Footer, Static

from app.tui.registry import Feature

PHASE_NOTES = {
    2: "Interactive Workspace & AI Agent",
    3: "Rich Data & Report Viewer",
    4: "Productivity: search, shortcut, session",
}


class PlannedScreen(Screen):
    BINDINGS = [
        Binding("escape", "back", "Kembali"),
        Binding("b", "back", "Kembali"),
    ]

    def __init__(self, feature: Feature) -> None:
        super().__init__()
        self._feature = feature

    def compose(self) -> ComposeResult:
        phase = self._feature.planned_phase or 0
        note = PHASE_NOTES.get(phase, "")
        yield Static(
            f"[bold]{self._feature.title}[/]\n\n"
            f"{self._feature.description}\n\n"
            f"Tersedia di Phase {self._feature.planned_phase} — {note}\n\n"
            "[dim]Fitur ini hadir lewat TUI pada phase tersebut.[/dim]"
        )
        yield Footer()

    def action_back(self) -> None:
        self.app.pop_screen()
