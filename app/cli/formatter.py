from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from app.models.stock import StockData
from app.models.analysis import AIAnalysis
from app.screeners.engine import ScreeningResult

console = Console()


def print_stock_header(data: StockData) -> None:
    text = Text()
    text.append(f"{data.info.ticker}", style="bold cyan")
    text.append(f" - {data.info.name}", style="white")
    if data.info.sector:
        text.append(f"\nSektor: {data.info.sector}", style="dim")
    if data.info.market_cap:
        text.append(f" | Market Cap: Rp{data.info.market_cap:,.0f}", style="dim")
    console.print(Panel(text, title="[bold]Stock Info[/bold]"))


def print_screening_results(results: list[ScreeningResult]) -> None:
    if not results:
        console.print("[yellow]Tidak ada sinyal screening ditemukan.[/yellow]")
        return
    table = Table(title="Hasil Screening")
    table.add_column("Sinyal", style="bold")
    table.add_column("Alasan")
    table.add_column("Confidence")
    for r in results:
        signal_style = "green" if r.signal == "BUY" else "red" if r.signal == "SELL" else "yellow"
        table.add_row(f"[{signal_style}]{r.signal}[/{signal_style}]", r.reason, f"{r.confidence:.0%}")
    console.print(table)


def print_bulk_screening(results: list[dict], title: str = "Hasil Screening") -> None:
    if not results:
        console.print("[yellow]Tidak ada sinyal screening ditemukan.[/yellow]")
        return
    table = Table(title=title)
    table.add_column("Ticker", style="cyan")
    table.add_column("Nama")
    table.add_column("Sektor")
    table.add_column("Harga")
    table.add_column("Sinyal", style="bold")
    table.add_column("Confidence")
    for r in results:
        ts = r["top_signal"]
        signal_style = "green" if ts.signal == "BUY" else "red" if ts.signal == "SELL" else "yellow"
        table.add_row(
            r["ticker"],
            r.get("name", "")[:25],
            (r.get("sector") or "")[:15],
            f"{r.get('price', 0):,.0f}",
            f"[{signal_style}]{ts.signal}[/{signal_style}]",
            f"{ts.confidence:.0%}",
        )
    console.print(table)


def print_gainer_loser_table(results: list[dict], title: str = "Top") -> None:
    if not results:
        console.print("[yellow]Tidak ada data.[/yellow]")
        return
    table = Table(title=title)
    table.add_column("#", style="dim")
    table.add_column("Ticker", style="cyan")
    table.add_column("Harga")
    table.add_column("Perubahan")
    for i, r in enumerate(results, 1):
        change = r.get("change", 0)
        style = "green" if change >= 0 else "red"
        table.add_row(str(i), r["ticker"], f"{r['price']:,.0f}", f"[{style}]{change:+.2f}%[/{style}]")
    console.print(table)


def print_price_info(data: StockData) -> None:
    if not data.history:
        console.print("[red]Tidak ada data harga.[/red]")
        return
    last = data.history[-1]
    prev = data.history[-2] if len(data.history) > 1 else None
    change = last.close - prev.close if prev else 0.0
    pct = (change / prev.close * 100) if prev and prev.close != 0 else 0.0
    change_style = "green" if change >= 0 else "red"
    console.print(Panel(
        f"Harga: [bold]{last.close:,.0f}[/bold]  "
        f"Range: {last.low:,.0f} - {last.high:,.0f}  "
        f"Volume: {last.volume:,}\n"
        f"Perubahan: [{change_style}]{change:+,.0f} ({pct:+.2f}%)[/{change_style}]",
        title="[bold]Price[/bold]"
    ))


def print_ai_analysis(result: AIAnalysis) -> None:
    header = Text()
    header.append(f"{result.ticker}", style="bold cyan")
    if result.raw_data:
        header.append(f" - {result.raw_data.info.name}", style="white")
    console.print(Panel(header, title="[bold]AI Analysis[/bold]"))
    if result.summary:
        console.print(result.summary)
    if result.key_metrics:
        table = Table(title="Metrik Kunci")
        table.add_column("Indikator", style="cyan")
        table.add_column("Nilai", style="white")
        for k, v in result.key_metrics.items():
            table.add_row(k, str(v))
        console.print(table)
    if result.risks:
        risks_text = "\n".join(f"• {r}" for r in result.risks)
        console.print(Panel(risks_text, title="[bold red]Risiko[/bold red]", border_style="red"))
    if result.conclusion:
        console.print(Panel(result.conclusion, title="[bold green]Kesimpulan[/bold green]", border_style="green"))
    if result.screening_results:
        print_screening_results(result.screening_results)


def print_error(message: str) -> None:
    console.print(f"[bold red]Error:[/bold red] {message}")


def print_info(message: str) -> None:
    console.print(f"[bold blue]Info:[/bold blue] {message}")
