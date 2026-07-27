import sys
import typer
from app.config.settings import settings
from app.utils.logging import setup_logging
from app.agent.core import analyze_with_ai, compare_with_ai, ask_llm
from app.agent.research import run_research
from app.router.engine import fetch_stock, build_context, run_screening, bulk_screen, bulk_gainers, bulk_losers
from app.services.stock_list import get_all, search
from app.presenters.rich_presenter import console, RichPresenter
from app.parser.intent import INTENT_UNKNOWN, INTENT_RESEARCH, parse
from app.services.validate_universe import run as validate_run, last_validated_days
from app.validation import validate as validate_symbol
from typing import Optional

_p = RichPresenter()


def _warn_universe_age():
    days = last_validated_days()
    if days is not None and days > 7:
        console.print(f"[dim]Data universe: {int(days)} hari, jalankan 'screening validate-universe' untuk update[/dim]")


_KNOWN_COMMANDS = {"analyze", "trend", "score", "compare", "screen", "gainers",
                   "losers", "sector", "stocks", "natural", "info", "chat", "research", "validate-universe"}

def _reroute_unknown_to_natural():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    if args and args[0].lower() not in _KNOWN_COMMANDS:
        sys.argv.insert(1, "natural")

_reroute_unknown_to_natural()

app = typer.Typer()


@app.callback()
def main() -> None:
    setup_logging(settings.log_level)


@app.command()
def analyze(ticker: str) -> None:
    err = validate_symbol(ticker)
    if err:
        _p.error(err)
        raise typer.Exit(1)
    with console.status(f"[bold blue]Menganalisis {ticker.upper()}..."):
        result = analyze_with_ai(ticker)
    _p.analysis(result)


@app.command()
def trend(ticker: str) -> None:
    err = validate_symbol(ticker)
    if err:
        _p.error(err)
        raise typer.Exit(1)
    data = fetch_stock(ticker)
    if not data:
        _p.error(f"Data untuk {ticker.upper()} tidak ditemukan")
        raise typer.Exit(1)
    ctx = build_context(data)
    _p.stock_header(data)
    info_text = f"Indikator: {ctx['indicators']}\nScreening: {ctx['screening']}"
    console.print(f"[bold]Info Teknikal:[/bold]\n{info_text}")


@app.command()
def score(ticker: str) -> None:
    err = validate_symbol(ticker)
    if err:
        _p.error(err)
        raise typer.Exit(1)
    data = fetch_stock(ticker)
    if not data:
        _p.error(f"Data untuk {ticker.upper()} tidak ditemukan")
        raise typer.Exit(1)
    results = run_screening(data)
    _p.stock_header(data)
    if results:
        _p._print_screening_results(results)
    else:
        _p.info("Tidak ada sinyal screening ditemukan")


@app.command()
def compare(
    ticker1: str = typer.Argument(help="Ticker pertama (atau dua ticker pisah koma)"),
    ticker2: str = typer.Argument("", help="Ticker kedua (opsional)"),
) -> None:
    tickers_str = f"{ticker1},{ticker2}" if ticker2 else ticker1
    tickers = [t.strip().upper() for t in tickers_str.replace(",", " ").split()]
    for t in tickers:
        err = validate_symbol(t)
        if err:
            _p.error(err)
            raise typer.Exit(1)
    with console.status(f"[bold blue]Membandingkan {', '.join(tickers)}..."):
        result = compare_with_ai(tickers)
    if result["type"] == "error":
        _p.error(result["message"])
        raise typer.Exit(1)
    if result.get("analysis"):
        console.print(result["analysis"])
    else:
        _p.error("Analisis tidak tersedia")


@app.command()
def screen(
    sector: Optional[str] = typer.Option(None, "--sector", "-s", help="Filter sektor"),
    limit: int = typer.Option(10, "--limit", "-n", help="Jumlah maksimal hasil"),
) -> None:
    _warn_universe_age()
    tickers = [s["ticker"] for s in get_all()]
    with console.status(f"[bold blue]Screening saham..."):
        results, invalid, failed = bulk_screen(tickers)
    if sector:
        results = [r for r in results if r.get("sector") and sector.lower() in r["sector"].lower()]
    if limit:
        results = results[:limit]
    if not results:
        _p.info("Tidak ada sinyal screening ditemukan")
        if invalid:
            console.print(f"[dim]{len(invalid)} ticker tidak ditemukan[/dim]")
        if failed:
            console.print(f"[yellow]⚠ {len(failed)} saham gagal diproses[/yellow]")
        return
    _print_bulk_screening(results, title=f"Hasil Screening{' — ' + sector if sector else ''}", invalid=invalid, failed=failed)


@app.command()
def gainers(limit: int = 10) -> None:
    _warn_universe_age()
    tickers = [s["ticker"] for s in get_all()]
    with console.status(f"[bold blue]Mengambil harga {len(tickers)} saham..."):
        results, invalid, failed = bulk_gainers(tickers)
    _print_bulk_change(results[:limit], title="Top Gainers", invalid=invalid, failed=failed)


@app.command()
def losers(limit: int = 10) -> None:
    _warn_universe_age()
    tickers = [s["ticker"] for s in get_all()]
    with console.status(f"[bold blue]Mengambil harga {len(tickers)} saham..."):
        results, invalid, failed = bulk_losers(tickers)
    _print_bulk_change(results[:limit], title="Top Losers", invalid=invalid, failed=failed)


@app.command()
def sector(name: str = typer.Argument(help="Nama sektor, contoh: Financials")) -> None:
    _warn_universe_age()
    tickers = [s["ticker"] for s in get_all()]
    with console.status(f"[bold blue]Screening saham sektor {name}..."):
        results, invalid, failed = bulk_screen(tickers)
    results = [r for r in results if r.get("sector") and name.lower() in r["sector"].lower()]
    if not results:
        _p.info(f"Tidak ada sinyal screening di sektor {name}")
        if invalid:
            console.print(f"[dim]{len(invalid)} ticker tidak ditemukan[/dim]")
        if failed:
            console.print(f"[yellow]⚠ {len(failed)} saham gagal diproses[/yellow]")
        return
    _print_bulk_screening(results, title=f"Hasil Screening — {name}", invalid=invalid, failed=failed)


@app.command()
def stocks(query: Optional[str] = typer.Argument(None, help="Cari kode/nama saham")) -> None:
    all_stocks = search(query) if query else get_all()
    console.print(f"[bold]Total: {len(all_stocks)} saham[/bold]")
    for s in all_stocks[:30]:
        console.print(f"  [cyan]{s['ticker']}[/cyan] - {s['name']}")
    if len(all_stocks) > 30:
        console.print(f"  ... dan {len(all_stocks) - 30} lainnya (gunakan filter untuk spesifik)")


@app.command()
def natural(query: str) -> None:
    intent, params = parse(query)
    if intent == "analyze":
        analyze(params.get("ticker", ""))
    elif intent == "compare":
        tk = params.get("tickers", "")
        compare(tk)
    elif intent == "screen":
        sector_filter = params.get("sector")
        screen(sector=sector_filter)
    elif intent == "research":
        research(params.get("text", query))
    elif intent == "help":
        info()
    else:
        resp = ask_llm(query)
        if resp:
            console.print(resp)
        else:
            _p.error("Query tidak dikenali. Coba: 'analisa BBCA', 'bandingkan BBCA dan BBRI', 'info'")


@app.command()
def research(query: str) -> None:
    with console.status(f"[bold blue]Menjalankan riset untuk: {query}..."):
        report = run_research(query)
    _p.research_report(report)


@app.command()
def chat() -> None:
    console.print("[bold]Mode diskusi. Ketik 'exit' atau Ctrl-C untuk keluar.[/bold]")
    messages: list[dict] = []
    while True:
        try:
            query = console.input("[bold cyan]>> [/bold cyan]")
            if query.lower() in ("exit", "quit", "keluar"):
                break
            resp = ask_llm(query, messages=messages)
            if resp:
                console.print(resp)
                messages.append({"role": "user", "content": query})
                messages.append({"role": "assistant", "content": resp})
            else:
                _p.error("AI tidak merespon. Periksa konfigurasi .env")
        except (EOFError, KeyboardInterrupt):
            console.print()
            break


@app.command()
def validate_universe(dry_run: bool = typer.Option(False, "--dry-run", help="Hanya laporan, tidak ubah file")) -> None:
    """Validasi daftar emiten via Yahoo Finance. Update valid flag."""
    with console.status("[bold blue]Memvalidasi daftar emiten..."):
        validate_run(dry_run=dry_run)


@app.command()
def info() -> None:
    console.print("[bold]Available commands:[/bold]")
    console.print("  analyze [ticker]     - Analisa saham (AI)")
    console.print("  trend [ticker]       - Trend teknikal saham")
    console.print("  score [ticker]       - Screening score saham")
    console.print("  compare [t1] [t2]    - Bandingkan dua saham")
    console.print("  screen [opts]        - Bulk screening (--sector, --limit)")
    console.print("  gainers              - Top gainers")
    console.print("  losers               - Top losers")
    console.print('  sector [name]        - Screening by sector, contoh: "sector Financials"')
    console.print("  stocks [query]       - Daftar saham")
    console.print("  chat                 - Mode diskusi interaktif")
    console.print('  "[query]"            - Bahasa natural (contoh: "BBCA" atau "analisa BBCA")')
    console.print("  research [query]     - Riset end-to-end (screening+analisis+perbandingan)")
    console.print("  validate-universe    - Validasi ulang daftar emiten via Yahoo Finance")
    console.print("  info                 - Bantuan ini")


def _print_bulk_screening(results: list[dict], title: str = "Hasil Screening", invalid: list[str] | None = None, failed: list[str] | None = None) -> None:
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


def _print_bulk_change(results: list[dict], title: str = "Top", invalid: list[str] | None = None, failed: list[str] | None = None) -> None:
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


if __name__ == "__main__":
    app()
