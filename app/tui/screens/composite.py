import asyncio
import json

from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Label, Static

from app.tui.executor import Executor, terminate_process
from app.tui.registry import Feature

_RATIO_LABELS = (("per", "PER"), ("pbv", "PBV"), ("der", "DER"), ("roe", "ROE"), ("npm", "NPM"), ("roa", "ROA"))
_BLOCK_LABELS = {"quote": "Quote", "stats": "Statistik", "signal": "Sinyal", "narrative": "Narasi AI"}


class CompositeViewScreen(Screen):
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
        yield Static(f"[bold]{self._feature.title}[/] — {self._feature.description}", id="subtitle")
        yield Static("", id="header")
        yield Label("Memproses...", id="status")
        yield Static("", id="quote")
        yield Static("", id="stats")
        yield Label("", id="signal")
        yield Static("", id="narrative")
        yield Footer()

    def on_mount(self) -> None:
        self._load()

    @work(exclusive=True)
    async def _load(self) -> None:
        proc = self._executor.run(self._argv + ["--json"])
        try:
            out, _err = await asyncio.to_thread(proc.communicate)
        finally:
            terminate_process(proc)
        self.query_one("#status", Label).update("")
        if not out.strip():
            self.query_one("#header", Static).update("[red]Perintah tidak menghasilkan output[/red]")
            return
        try:
            data = json.loads(out)
        except json.JSONDecodeError:
            self.query_one("#header", Static).update("[red]Output bukan JSON[/red]")
            return
        self._render_blocks(data)

    def _render_blocks(self, data: dict) -> None:
        blocks = data.get("blocks") or {}
        self.query_one("#header", Static).update(f"[bold]{data.get('name') or data.get('ticker', '')}[/]")
        self._render_quote(blocks.get("quote"))
        self._render_stats(blocks.get("stats"))
        self._render_signal(blocks.get("signal"))
        self._render_narrative(blocks.get("narrative"))

    def _render_quote(self, block) -> None:
        if block is None or block.get("status") != "available":
            self.query_one("#quote", Static).update("[yellow]⚠ Quote: data tidak tersedia[/yellow]")
            return
        d = block.get("data") or {}
        name = d.get("name") or ""
        sector = f" | Sektor: {d['sector']}" if d.get("sector") else ""
        price = f"{d.get('price', 0):,.0f}"
        change = d.get("change") or "0%"
        self.query_one("#quote", Static).update(
            f"[bold]{name}[/]{sector}\nHarga: [cyan]{price}[/] | Perubahan: {change}"
        )

    def _render_stats(self, block) -> None:
        if block is None or block.get("status") not in ("available", "partial"):
            self.query_one("#stats", Static).update("[yellow]⚠ Statistik: data tidak tersedia[/yellow]")
            return
        d = block.get("data") or {}
        lines = []
        if d.get("indicators"):
            lines.append(f"Indikator: {d['indicators']}")
        for key, label in _RATIO_LABELS:
            v = d.get(key)
            if isinstance(v, dict):
                v = v.get("latest")
            if v is not None:
                try:
                    lines.append(f"{label}: {v:.4f}".rstrip("0").rstrip("."))
                except (TypeError, ValueError):
                    lines.append(f"{label}: {v}")
        text = "\n".join(lines) if lines else "Tidak ada data statistik"
        if block.get("status") == "partial":
            text += f"\n[yellow]⚠ Sebagian tidak tersedia: {block.get('error', '')}[/yellow]"
        self.query_one("#stats", Static).update(text)

    def _render_signal(self, block) -> None:
        if block is None or block.get("status") != "available":
            self.query_one("#signal", Label).update("⚠ Sinyal: data tidak tersedia")
            return
        signs = (block.get("data") or {}).get("signals") or []
        if not signs:
            self.query_one("#signal", Label).update("[dim]Tidak ada sinyal screening[/dim]")
            return
        lines = []
        for s in signs:
            style = "green" if s.get("signal") == "BUY" else "red" if s.get("signal") == "SELL" else "yellow"
            conf = s.get("confidence", 0)
            lines.append(f"[{style}]{s.get('signal', '')}[/{style}] — {s.get('reason', '')} ({conf:.0%})")
        self.query_one("#signal", Label).update("\n".join(lines))

    def _render_narrative(self, block) -> None:
        if block is None or block.get("status") != "available":
            self.query_one("#narrative", Static).update("[yellow]⚠ Narasi AI: data tidak tersedia[/yellow]")
            return
        summary = (block.get("data") or {}).get("summary", "")
        if not summary:
            self.query_one("#narrative", Static).update("[yellow]⚠ Narasi AI: analisis tidak tersedia[/yellow]")
            return
        self.query_one("#narrative", Static).update(f"[dim]— Narasi AI —[/dim]\n{summary}\n[dim]——[/dim]")

    def action_back(self) -> None:
        self.app.pop_screen()