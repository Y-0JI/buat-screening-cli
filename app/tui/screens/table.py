import asyncio
import json

from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Label, Static

from app.tui.executor import Executor, terminate_process
from app.tui.registry import Feature


class ResultTableScreen(Screen):
    """Render output --json jadi tabel/panel (reusable utk semua data fitur)."""

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
        yield Static(f"[bold]{self._feature.title}[/]", id="subtitle")
        yield Label("", id="progress")
        yield DataTable(id="table", zebra_stripes=True)
        yield Footer()

    def on_mount(self) -> None:
        self._load()

    @work(exclusive=True)
    async def _load(self) -> None:
        self.query_one("#progress", Label).update("Memproses...")
        proc = self._executor.run(self._argv + ["--json"])
        try:
            out, _err = await asyncio.to_thread(proc.communicate)
        finally:
            terminate_process(proc)
        exit_code = proc.wait()
        self.query_one("#progress", Label).update("")
        if exit_code != 0 or not out.strip():
            self._show_rows([{"Keterangan": f"Perintah tidak menghasilkan output (exit {exit_code})"}])
            return
        try:
            data = json.loads(out)
        except json.JSONDecodeError:
            self._show_rows([{"Keterangan": "Output bukan JSON — fitur tidak mendukung tabel"}])
            return
        self._render_data(data)

    def _show_rows(self, rows: list[dict]) -> None:
        table = self.query_one(DataTable)
        table.clear(columns=True)
        if not rows:
            table.add_column("Hasil")
            table.add_row("Tidak ada data")
            return
        cols: list[str] = []
        seen: set[str] = set()
        for row in rows:
            for k in row.keys():
                if k not in seen:
                    seen.add(k)
                    cols.append(k)
        for k in cols:
            table.add_column(str(k))
        for row in rows:
            table.add_row(*[str(row.get(k, "")) for k in cols])

    def _render_data(self, data: dict) -> None:
        if "providers" in data:
            self._render_providers(data["providers"])
        elif "watchlist" in data:
            self._render_watchlist(data["watchlist"])
        elif "results" in data:
            notes = []
            if data.get("invalid"):
                notes.append(f"{len(data['invalid'])} tidak ditemukan")
            if data.get("failed"):
                notes.append(f"{len(data['failed'])} gagal diproses")
            if notes:
                self.query_one("#progress", Label).update(" · ".join(notes))
            self._show_rows([r for r in data["results"] if isinstance(r, dict)])
        else:
            self._show_rows([{"Keterangan": "Struktur data tidak dikenal"}])

    def _render_providers(self, providers: list[dict]) -> None:
        rows = [{"provider": p.get("name", ""), "status": p.get("status", "")} for p in providers]
        self._show_rows(rows)

    def _render_watchlist(self, w: dict) -> None:
        title = w.get("name", "")
        if w.get("favorite"):
            title += " ★"
        if w.get("tags"):
            title += " [" + ", ".join(w["tags"]) + "]"
        self.query_one("#subtitle", Static).update(f"[bold]{title}[/]")
        self._show_rows([e for e in w.get("entries") or [] if isinstance(e, dict)])

    def action_back(self) -> None:
        self.app.pop_screen()