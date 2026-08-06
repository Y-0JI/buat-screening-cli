from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Footer, Input, Label, Log

from app.tui.executor import Executor, stream_process, terminate_process
from app.tui.registry import Feature
from app.tui.session import load_history, save_history


class ChatScreen(Screen):
    BINDINGS = [
        Binding("escape", "back", "Kembali"),
        Binding("b", "back", "Kembali"),
    ]

    def __init__(self, feature: Feature, executor: Executor) -> None:
        super().__init__()
        self._feature = feature
        self._executor = executor
        self._lines: list[str] = []

    def compose(self) -> ComposeResult:
        yield Log(highlight=False, id="history")
        yield Label("", id="status")
        yield Input(placeholder="Tulis pesan...", id="prompt")
        yield Footer()

    def _write(self, line: str) -> None:
        self._lines.append(line)
        self.query_one(Log).write_line(line)

    def on_mount(self) -> None:
        self._lines = load_history()
        for line in self._lines:
            self.query_one(Log).write_line(line)
        self._write(f"{self._feature.title} — {self._feature.description}")
        self.query_one(Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        query = event.value.strip()
        if not query:
            return
        event.input.value = ""
        self._write(f"> {query}")
        self.query_one("#status", Label).update("Memproses...")
        self._send(query)

    @work(group="chat", exclusive=True)
    async def _send(self, query: str) -> None:
        argv = self._feature.command + [query]
        try:
            proc = self._executor.run(argv)
        except Exception as exc:
            self._write(f"✗ Gagal menjalankan: {exc}")
            self._write("")
            self.query_one("#status", Label).update("")
            return
        try:
            exit_code = await stream_process(proc, self._write)
        finally:
            terminate_process(proc)
        if exit_code == 0:
            self._write(f"✓ Selesai (exit {exit_code})")
        else:
            self._write(f"✗ Gagal (exit {exit_code})")
        self._write("")
        self.query_one("#status", Label).update("")

    def on_unmount(self) -> None:
        save_history(self._lines)

    def action_back(self) -> None:
        self.app.pop_screen()
