import asyncio
import json

from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Label, Static

from app.tui.executor import Executor
from app.tui.registry import Feature

_SECTION_LABELS = {
    "fundamental": "Fundamental",
    "financial": "Keuangan",
    "valuation": "Valuasi",
    "growth": "Pertumbuhan",
    "dividend": "Dividen",
    "technical": "Teknikal",
    "risk": "Risiko",
    "market": "Pasar",
    "market_intelligence": "Intelijen Pasar",
    "investment_conclusion": "Kesimpulan Investasi",
}


def _flatten(data: dict, prefix: str = "") -> list[tuple[str, str]]:
    rows = []
    for k, v in data.items():
        key = f"{prefix}{k}"
        if isinstance(v, dict):
            rows.extend(_flatten(v, f"{key}."))
        elif isinstance(v, list):
            text = "; ".join(str(x) for x in v[:8])
            if len(v) > 8:
                text += " ..."
            rows.append((key, text))
        else:
            rows.append((key, str(v)))
    return rows


class ReportViewerScreen(Screen):
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
        yield Static("", id="report-header")
        yield Label("Memproses...", id="status")
        yield DataTable(id="report", zebra_stripes=True, cursor_type="row")
        yield Footer()

    def on_mount(self) -> None:
        self._load()

    @work(exclusive=True)
    async def _load(self) -> None:
        proc = self._executor.run(self._argv + ["--json"])
        out, _err = await asyncio.to_thread(proc.communicate)
        proc.wait()
        self.query_one("#status", Label).update("")
        header = self.query_one("#report-header", Static)
        table = self.query_one(DataTable)
        table.add_column("Key")
        table.add_column("Value")
        if not out.strip():
            header.update("[red]Perintah tidak menghasilkan output[/red]")
            return
        try:
            data = json.loads(out)
        except json.JSONDecodeError:
            header.update("[red]Output bukan JSON[/red]")
            return
        self._render_report(data, header, table)

    def _render_report(self, data: dict, header: Static, table: DataTable) -> None:
        intent = data.get("intent") or {}
        query = intent.get("raw_query") or ""
        itype = intent.get("type") or ""
        title = f"[bold]Laporan Riset — {query}[/]"
        if itype:
            title += f" [dim]({itype})[/]"
        header.update(title)
        if data.get("ai_failed"):
            table.add_row("AI", "AI tidak tersedia — laporan dari data terkini")
        if data.get("failed"):
            table.add_row("Gagal", ", ".join(data["failed"]))
        if data.get("executive_summary"):
            table.add_row("Ringkasan Eksekutif", data["executive_summary"])

        sections = data.get("sections") or {}
        for key, sec in sections.items():
            status = sec.get("status", "missing")
            label = _SECTION_LABELS.get(key, key.replace("_", " ").title())
            if status == "missing":
                reason = sec.get("reason") or "data tidak tersedia"
                table.add_row(f"## {label} [tidak tersedia]", reason)
                continue
            badge = "[sebagian]" if status == "partial" else ""
            table.add_row(f"## {label} {badge}", "")
            for rk, rv in _flatten(sec.get("data") or {}):
                table.add_row(rk, rv)

        recommendations = data.get("recommendations") or []
        if recommendations:
            table.add_row("## Rekomendasi", "")
            for r in recommendations:
                table.add_row("-", str(r))

    def action_back(self) -> None:
        self.app.pop_screen()