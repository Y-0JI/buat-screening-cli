import subprocess

from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Footer, Label, Log

from app.tui.executor import Executor, stream_process
from app.tui.registry import Feature


def _terminate_proc(proc: subprocess.Popen) -> None:
    if proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()


class CommandViewerScreen(Screen):
    BINDINGS = [
        Binding("escape", "back", "Kembali"),
        Binding("b", "back", "Kembali"),
    ]

    def __init__(self, feature: Feature, argv: list[str], executor: Executor) -> None:
        super().__init__()
        self._feature = feature
        self._argv = argv
        self._executor = executor

    def compose(self) -> ComposeResult:
        yield Log(highlight=False, id="output")
        yield Label("Memproses...", id="status")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one(Log).write_line(f"$ screening {' '.join(self._argv)}")
        self._stream()

    @work(exclusive=True)
    async def _stream(self) -> None:
        log = self.query_one(Log)
        try:
            proc = self._executor.run(self._argv)
        except Exception as exc:
            log.write_line(f"✗ Gagal menjalankan: {exc}")
            return
        try:
            exit_code = await stream_process(proc, log.write_line)
        finally:
            _terminate_proc(proc)
        self.query_one("#status", Label).update("")
        if exit_code == 0:
            log.write_line(f"✓ Selesai (exit {exit_code})")
        else:
            log.write_line(f"✗ Gagal (exit {exit_code})")

    def action_back(self) -> None:
        self.app.pop_screen()