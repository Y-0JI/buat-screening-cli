from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from app.presenters.base import BasePresenter

console = Console()


class RichPresenter(BasePresenter):
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
            from app.screeners.engine import ScreeningResult
            from app.cli.formatter import print_screening_results
            print_screening_results(analysis.screening_results)

    def research_report(self, report) -> None:
        console.rule("[bold cyan]Laporan Riset End-to-End[/bold cyan]")
        console.print(f"[bold]Query:[/bold] {report.intent.raw_query}")
        console.print(f"[bold]Tipe Riset:[/bold] {report.intent.type}")
        console.print()

        if report.executive_summary:
            console.print(Panel(report.executive_summary, title="[bold]Ringkasan Eksekutif[/bold]", border_style="cyan"))
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
            console.print(Panel(report.comparison["analysis"], title="[bold]Perbandingan[/bold]", border_style="magenta"))
            console.print()

        if report.recommendations:
            rec_text = "\n".join(f"{i+1}. {r}" for i, r in enumerate(report.recommendations))
            console.print(Panel(rec_text, title="[bold green]Rekomendasi[/bold green]", border_style="green"))

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

    def stock_header(self, data) -> None:
        text = Text()
        text.append(f"{data.info.ticker}", style="bold cyan")
        text.append(f" - {data.info.name}", style="white")
        if data.info.sector:
            text.append(f"\nSektor: {data.info.sector}", style="dim")
        if data.info.market_cap:
            text.append(f" | Market Cap: Rp{data.info.market_cap:,.0f}", style="dim")
        console.print(Panel(text, title="[bold]Stock Info[/bold]"))
