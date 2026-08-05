from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Footer, Input, Log

from app.tui.executor import Executor
from app.tui.registry import Feature


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
        yield Input(placeholder="Tulis pesan...", id="prompt")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one(Log).write_line(f"[bold]{self._feature.title}[/] — {self._feature.description}")
        self.query_one(Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        query = event.value.strip()
        if not query:
            return
        event.input.value = ""
        log = self.query_one(Log)
        log.write_line(f"> {query}")
        self._send(query, log)

    @work(exclusive=True)
    async def _send(self, query: str, log: Log) -> None:
        argv = self._feature.command + [query]
        try:
            proc = self._executor.run(argv)
        except Exception as exc:
            log.write_line(f"✗ Gagal menjalankan: {exc}")
            log.write_line("")
            return
        for line in proc.stdout:
            log.write_line(line.rstrip("\n"))
        for line in proc.stderr:
            log.write_line(line.rstrip("\n"))
        exit_code = proc.wait()
        if exit_code == 0:
            log.write_line(f"✓ Selesai (exit {exit_code})")
        else:
            log.write_line(f"✗ Gagal (exit {exit_code})")
        log.write_line("")

    def action_back(self) -> None:
        self.app.pop_screen()