from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Footer, Log

from app.tui.executor import Executor
from app.tui.registry import Feature


class CommandViewerScreen(Screen):
    BINDINGS = [
        Binding("escape", "back", "Kembali"),
        Binding("b", "back", "Kembali"),
    ]

    def __init__(self, feature: Feature, executor: Executor) -> None:
        super().__init__()
        self._feature = feature
        self._executor = executor
        self._exit_code: int | None = None

    def compose(self) -> ComposeResult:
        yield Log(highlight=False, id="output")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one(Log).write_line(f"$ screening {' '.join(self._feature.command)}")
        self._stream()

    @work(exclusive=True)
    async def _stream(self) -> None:
        log = self.query_one(Log)
        try:
            proc = self._executor.run(self._feature)
        except Exception as exc:
            log.write_line(f"✗ Gagal menjalankan: {exc}")
            self._exit_code = 1
            return
        for line in proc.stdout:
            log.write_line(line.rstrip("\n"))
        for line in proc.stderr:
            log.write_line(line.rstrip("\n"))
        self._exit_code = proc.wait()
        if self._exit_code == 0:
            log.write_line(f"✓ Selesai (exit {self._exit_code})")
        else:
            log.write_line(f"✗ Gagal (exit {self._exit_code})")

    def action_back(self) -> None:
        self.app.pop_screen()
