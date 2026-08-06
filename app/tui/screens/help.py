from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Footer, Static

from app.tui.shortcuts import help_lines


class HelpScreen(Screen):
    BINDINGS = [
        Binding("escape", "back", "Kembali"),
        Binding("b", "back", "Kembali"),
    ]

    def compose(self) -> ComposeResult:
        rows = "".join(
            f"{key.ljust(12)} {desc}\n" if key else f"\n[bold]{desc}[/bold]\n"
            for key, desc in help_lines()
        )
        yield Static(f"[bold]Bantuan Keyboard[/bold]\n\n{rows}")
        yield Footer()

    def action_back(self) -> None:
        self.app.pop_screen()
