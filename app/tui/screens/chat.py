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

    def compose(self) -> ComposeResult:
        yield Log(highlight=False, id="history")
        yield Label("", id="status")
        yield Input(placeholder="Tulis pesan...", id="prompt")
        yield Footer()

    def on_mount(self) -> None:
        log = self.query_one(Log)
        log.write_line(f"{self._feature.title} — {self._feature.description}")
        for line in load_history():
            log.write_line(line)
        self.query_one(Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        query = event.value.strip()
        if not query:
            return
        event.input.value = ""
        self.query_one(Log).write_line(f"> {query}")
        self._send(query)

    @work(group="chat", exclusive=True)
    async def _send(self, query: str) -> None:
        log = self.query_one(Log)
        argv = self._feature.command + [query]
        try:
            proc = self._executor.run(argv)
        except Exception as exc:
            log.write_line(f"✗ Gagal menjalankan: {exc}")
            log.write_line("")
            return
        try:
            exit_code = await stream_process(proc, log.write_line)
        finally:
            terminate_process(proc)
        if exit_code == 0:
            log.write_line(f"✓ Selesai (exit {exit_code})")
        else:
            log.write_line(f"✗ Gagal (exit {exit_code})")
        log.write_line("")
        self.query_one("#status", Label).update("")

    def action_back(self) -> None:
        save_history(self.query_one(Log).lines)
        self.app.pop_screen()