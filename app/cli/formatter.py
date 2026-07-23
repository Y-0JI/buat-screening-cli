from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from app.models.stock import StockData
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
    table.add_column("Ticker", style="cyan")
    table.add_column("Sinyal", style="bold")
    table.add_column("Alasan")
    table.add_column("Confidence")
    for r in results:
        signal_style = "green" if r.signal == "BUY" else "red" if r.signal == "SELL" else "yellow"
        table.add_row(r.ticker, f"[{signal_style}]{r.signal}[/{signal_style}]", r.reason, f"{r.confidence:.0%}")
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


def print_error(message: str) -> None:
    console.print(f"[bold red]Error:[/bold red] {message}")


def print_info(message: str) -> None:
    console.print(f"[bold blue]Info:[/bold blue] {message}")
