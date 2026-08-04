from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from app.models.research import REPORT_SECTION_LABELS, SectionStatus


console = Console()


class RichPresenter:
    def analysis(self, analysis) -> None:
        header = Text()
        header.append(f"{analysis.ticker}", style="bold cyan")
        if analysis.raw_data:
            header.append(f" - {analysis.raw_data.info.name}", style="white")
        console.print(Panel(header, title="[bold]AI Analysis[/bold]"))
        if analysis.summary:
            console.print(analysis.summary)
        if analysis.key_metrics:
            table = Table(title="Metrik Kunci")
            table.add_column("Indikator", style="cyan")
            table.add_column("Nilai", style="white")
            for k, v in analysis.key_metrics.items():
                table.add_row(k, str(v))
            console.print(table)
        if analysis.risks:
            risks_text = "\n".join(f"• {r}" for r in analysis.risks)
            console.print(Panel(risks_text, title="[bold red]Risiko[/bold red]", border_style="red"))
        if analysis.conclusion:
            console.print(Panel(analysis.conclusion, title="[bold green]Kesimpulan[/bold green]", border_style="green"))
        if analysis.screening_results:
            self._print_screening_results(analysis.screening_results)

    def comparison(self, result: dict) -> None:
        if result.get("analysis"):
            console.print(Panel(result["analysis"], title="[bold]Perbandingan[/bold]", border_style="magenta"))

    def research_report(self, report) -> None:
        console.rule("[bold cyan]Laporan Riset End-to-End[/bold cyan]")
        console.print(f"[bold]Query:[/bold] {report.intent.raw_query}")
        console.print(f"[bold]Tipe Riset:[/bold] {report.intent.type}")
        rd = report.research_data
        if rd:
            console.print(f"[bold]Simbol:[/bold] {rd.symbol}")
            console.print(f"[bold]Waktu dibuat:[/bold] {rd.created_at.strftime('%Y-%m-%d %H:%M UTC')}")
        console.print()

        if report.failed:
            console.print(f"[yellow]⚠ Gagal memuat data: {', '.join(report.failed)}[/yellow]")
            console.print()

        if report.ai_failed:
            console.print("[yellow]⚠ AI tidak tersedia — laporan otomatis dari data terkini. ResearchData tetap tersimpan untuk regenerasi.[/yellow]")
            console.print()

        if rd and report.ai_failed:
            from app.agent.research import serialize_research_data
            fallback = [l for l in serialize_research_data(rd).splitlines() if l not in ("## Ringkasan Eksekutif", "## Rekomendasi")]
            if fallback:
                console.print(Panel("\n".join(fallback), title="[bold]Data Terkini (fallback tanpa AI)[/bold]", border_style="blue"))
                console.print()

        if report.executive_summary:
            console.print(Panel(report.executive_summary, title="[bold]Ringkasan Eksekutif[/bold]", border_style="cyan"))
            console.print()

        if rd:
            for key in ("fundamental", "financial", "valuation", "growth", "dividend", "technical", "risk"):
                sec = rd.sections.get(key)
                if not sec or sec.status == SectionStatus.MISSING or not sec.data:
                    continue
                self._section_table(REPORT_SECTION_LABELS.get(key, key.replace("_", " ")), sec.data)

        if rd:
            missing = [s for s in rd.sections.items() if s[1].status.value == "missing"]
            if missing:
                labels = [f"{k.replace('_', ' ')} ({s.reason})" if s.reason else k.replace("_", " ") for k, s in missing]
                console.print(f"[dim]Data tidak tersedia: {', '.join(labels)}[/dim]")
                console.print()
            partial = [s for s in rd.sections.items() if s[1].status.value == "partial"]
            if partial:
                labels = [f"{k.replace('_', ' ')} ({s.reason})" if s.reason else k.replace("_", " ") for k, s in partial]
                console.print(f"[yellow]Data sebagian: {', '.join(labels)}[/yellow]")
                console.print()

        if report.screening_results:
            table = Table(title="Hasil Screening")
            table.add_column("Ticker", style="cyan")
            table.add_column("Sektor")
            table.add_column("Sinyal", style="bold")
            table.add_column("Confidence")
            for r in report.screening_results[:15]:
                ts = r.get("top_signal")
                signal_style = "green" if ts and ts.signal == "BUY" else "red" if ts and ts.signal == "SELL" else "yellow"
                table.add_row(r["ticker"], r.get("sector", "")[:15], f"[{signal_style}]{ts.signal if ts else 'N/A'}[/{signal_style}]", f"{ts.confidence:.0%}" if ts else "0%")
            console.print(table)
            console.print()

        if report.analyses:
            for ticker, a in report.analyses.items():
                header = f"{ticker}"
                if report.data_quality.get(ticker):
                    header += f" ⚠ {', '.join(report.data_quality[ticker])}"
                console.print(Panel(a.summary, title=f"[bold]Analisis {header}[/bold]", border_style="blue"))
                console.print()

        if report.comparison and report.comparison.get("analysis"):
            self.comparison(report.comparison)
            console.print()

        if report.recommendations:
            rec_text = "\n".join(f"{i+1}. {r}" for i, r in enumerate(report.recommendations))
            console.print(Panel(rec_text, title="[bold green]Rekomendasi[/bold green]", border_style="green"))

        if rd and rd.sections.get("investment_conclusion") and rd.sections["investment_conclusion"].data:
            conf = rd.sections["investment_conclusion"].data.get("confidence", {})
            lines = [f"Level: {conf.get('confidence_level', '?')} (skor {conf.get('confidence_score', '?')})"]
            for label, key in (("Mengurangi", "missing_sections"), ("Sebagian", "partial_sections")):
                items = conf.get(key) or {}
                if items:
                    lines.append(f"{label}: " + ", ".join(f"{k} ({r})" if r else k for k, r in items.items()))
            console.print()
            console.print(Panel("\n".join(lines), title="[bold]Confidence (kelengkapan data)[/bold]", border_style="magenta"))

    def _section_table(self, title: str, data: dict) -> None:
        from app.agent.research import _fmt_num
        table = Table(title=title)
        table.add_column("Label", style="cyan")
        table.add_column("Nilai", style="white")
        for ticker, metrics in data.items():
            items = metrics.items() if isinstance(metrics, dict) else ((ticker, metrics),)
            prefix = f"{ticker}." if isinstance(metrics, dict) and len(data) > 1 else ""
            for k, v in items:
                if isinstance(v, dict):
                    parts = ", ".join(f"{sk}={_fmt_num(sv)}" for sk, sv in v.items() if sv is not None)
                    table.add_row(f"{prefix}{k}", parts)
                elif isinstance(v, list):
                    table.add_row(f"{prefix}{k}", "; ".join(str(x) for x in v))
                else:
                    table.add_row(f"{prefix}{k}", _fmt_num(v))
        console.print(table)
        console.print()

    def error(self, message: str) -> None:
        console.print(f"[bold red]Error:[/bold red] {message}")

    def info(self, message: str) -> None:
        console.print(f"[bold blue]Info:[/bold blue] {message}")

    def table(self, title: str, columns, rows) -> None:
        table = Table(title=title)
        for name, style in columns:
            table.add_column(name, style=style)
        for row in rows:
            table.add_row(*row)
        console.print(table)

    def _print_screening_results(self, results) -> None:
        if not results:
            console.print("[yellow]Tidak ada sinyal screening ditemukan.[/yellow]")
            return
        cols = [("Sinyal", "bold"), ("Alasan", ""), ("Confidence", "")]
        rows = []
        for r in results:
            style = "green" if r.signal == "BUY" else "red" if r.signal == "SELL" else "yellow"
            rows.append([f"[{style}]{r.signal}[/{style}]", r.reason, f"{r.confidence:.0%}"])
        self.table("Hasil Screening", cols, rows)

    def stock_header(self, data) -> None:
        text = Text()
        text.append(f"{data.info.ticker}", style="bold cyan")
        text.append(f" - {data.info.name}", style="white")
        if data.info.sector:
            text.append(f"\nSektor: {data.info.sector}", style="dim")
        if data.info.market_cap:
            text.append(f" | Market Cap: Rp{data.info.market_cap:,.0f}", style="dim")
        console.print(Panel(text, title="[bold]Stock Info[/bold]"))
