from app.presenters import RichPresenter
from app.presenters.rich_presenter import console

_p = RichPresenter()


def print_stock_header(data) -> None:
    _p.stock_header(data)


def print_screening_results(results) -> None:
    if not results:
        console.print("[yellow]Tidak ada sinyal screening ditemukan.[/yellow]")
        return
    cols = [("Sinyal", "bold"), ("Alasan", ""), ("Confidence", "")]
    rows = []
    for r in results:
        style = "green" if r.signal == "BUY" else "red" if r.signal == "SELL" else "yellow"
        rows.append([f"[{style}]{r.signal}[/{style}]", r.reason, f"{r.confidence:.0%}"])
    _p.table("Hasil Screening", cols, rows)


def print_bulk_screening(results: list[dict], title: str = "Hasil Screening", invalid: list[str] | None = None, failed: list[str] | None = None) -> None:
    if not results:
        console.print("[yellow]Tidak ada sinyal screening ditemukan.[/yellow]")
        if invalid:
            console.print(f"[dim]{len(invalid)} ticker tidak ditemukan[/dim]")
        if failed:
            console.print(f"[yellow]⚠ {len(failed)} saham gagal diproses[/yellow]")
        return
    from rich.table import Table
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
            r["ticker"], r.get("name", "")[:25], (r.get("sector") or "")[:15],
            f"{r.get('price', 0):,.0f}", f"[{signal_style}]{ts.signal}[/{signal_style}]", f"{ts.confidence:.0%}",
        )
    console.print(table)
    if invalid:
        console.print(f"[dim]{len(invalid)} ticker tidak ditemukan[/dim]")
    if failed:
        console.print(f"[yellow]⚠ {len(failed)} saham gagal diproses[/yellow]")


def print_gainer_loser_table(results: list[dict], title: str = "Top", invalid: list[str] | None = None, failed: list[str] | None = None) -> None:
    if not results:
        console.print("[yellow]Tidak ada data.[/yellow]")
        if invalid:
            console.print(f"[dim]{len(invalid)} ticker tidak ditemukan[/dim]")
        if failed:
            console.print(f"[yellow]⚠ {len(failed)} saham gagal diproses[/yellow]")
        return
    from rich.table import Table
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
    if invalid:
        console.print(f"[dim]{len(invalid)} ticker tidak ditemukan[/dim]")
    if failed:
        console.print(f"[yellow]⚠ {len(failed)} saham gagal diproses[/yellow]")


def print_price_info(data) -> None:
    if not data.history:
        console.print("[red]Tidak ada data harga.[/red]")
        return
    from rich.panel import Panel
    last = data.history[-1]
    prev = data.history[-2] if len(data.history) > 1 else None
    change = last.close - prev.close if prev else 0.0
    pct = (change / prev.close * 100) if prev and prev.close != 0 else 0.0
    change_style = "green" if change >= 0 else "red"
    console.print(Panel(
        f"Harga: [bold]{last.close:,.0f}[/bold]  Range: {last.low:,.0f} - {last.high:,.0f}  Volume: {last.volume:,}\n"
        f"Perubahan: [{change_style}]{change:+,.0f} ({pct:+.2f}%)[/{change_style}]",
        title="[bold]Price[/bold]",
    ))


def print_ai_analysis(result) -> None:
    _p.analysis(result)


def print_error(message: str) -> None:
    _p.error(message)


def print_info(message: str) -> None:
    _p.info(message)


def print_research_report(report) -> None:
    _p.research_report(report)