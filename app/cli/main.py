import sys
import typer
from app.config.settings import settings
from app.utils.logging import setup_logging
from app.agent.core import analyze_with_ai, compare_with_ai, ask_llm
from app.cli.formatter import print_ai_analysis, print_error, print_info, console
from app.router.engine import fetch_stock, build_context, run_screening, bulk_screen, bulk_gainers, bulk_losers
from app.cli.formatter import print_stock_header, print_screening_results, print_bulk_screening, print_gainer_loser_table
from app.parser.intent import INTENT_UNKNOWN, parse
from app.services.stock_list import get_all, search
from typing import Optional

_KNOWN_COMMANDS = {"analyze", "trend", "score", "compare", "screen", "gainers",
                   "losers", "sector", "stocks", "natural", "info"}

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
    result = analyze_with_ai(ticker)
    print_ai_analysis(result)


@app.command()
def trend(ticker: str) -> None:
    data = fetch_stock(ticker)
    if not data:
        print_error(f"Data untuk {ticker.upper()} tidak ditemukan")
        raise typer.Exit(1)
    ctx = build_context(data)
    print_stock_header(data)
    info_text = f"Indikator: {ctx['indicators']}\nScreening: {ctx['screening']}"
    console.print(f"[bold]Info Teknikal:[/bold]\n{info_text}")


@app.command()
def score(ticker: str) -> None:
    data = fetch_stock(ticker)
    if not data:
        print_error(f"Data untuk {ticker.upper()} tidak ditemukan")
        raise typer.Exit(1)
    results = run_screening(data)
    print_stock_header(data)
    print_screening_results(results)


@app.command()
def compare(
    ticker1: str = typer.Argument(help="Ticker pertama (atau dua ticker pisah koma)"),
    ticker2: str = typer.Argument("", help="Ticker kedua (opsional)"),
) -> None:
    tickers_str = f"{ticker1},{ticker2}" if ticker2 else ticker1
    tickers = [t.strip().upper() for t in tickers_str.replace(",", " ").split()]
    result = compare_with_ai(tickers)
    if result["type"] == "error":
        print_error(result["message"])
        raise typer.Exit(1)
    if result.get("analysis"):
        console.print(result["analysis"])
    else:
        print_error("Analisis tidak tersedia")


@app.command()
def screen(
    sector: Optional[str] = typer.Option(None, "--sector", "-s", help="Filter sektor"),
    limit: int = typer.Option(10, "--limit", "-n", help="Jumlah maksimal hasil"),
) -> None:
    tickers = [s["ticker"] for s in get_all()]
    with console.status(f"[bold blue]Screening {len(tickers)} saham..."):
        results = bulk_screen(tickers)
    if sector:
        results = [r for r in results if r.get("sector") and sector.lower() in r["sector"].lower()]
    if limit:
        results = results[:limit]
    if not results:
        print_info("Tidak ada sinyal screening ditemukan")
        return
    print_bulk_screening(results, title=f"Hasil Screening{' — ' + sector if sector else ''}")


@app.command()
def gainers(limit: int = 10) -> None:
    tickers = [s["ticker"] for s in get_all()]
    with console.status(f"[bold blue]Mengambil harga {len(tickers)} saham..."):
        results = bulk_gainers(tickers)
    print_gainer_loser_table(results[:limit], title="Top Gainers")


@app.command()
def losers(limit: int = 10) -> None:
    tickers = [s["ticker"] for s in get_all()]
    with console.status(f"[bold blue]Mengambil harga {len(tickers)} saham..."):
        results = bulk_losers(tickers)
    print_gainer_loser_table(results[:limit], title="Top Losers")


@app.command()
def sector(name: str = typer.Argument(help="Nama sektor, contoh: Financials")) -> None:
    tickers = [s["ticker"] for s in get_all()]
    with console.status(f"[bold blue]Screening {len(tickers)} saham sektor {name}..."):
        results = bulk_screen(tickers)
    filtered = [r for r in results if r.get("sector") and name.lower() in r["sector"].lower()]
    if not filtered:
        print_info(f"Tidak ada sinyal screening di sektor {name}")
        return
    print_bulk_screening(filtered, title=f"Hasil Screening — {name}")


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
    elif intent == "help":
        info()
    else:
        resp = ask_llm(query)
        if resp:
            console.print(resp)
        else:
            print_error("Query tidak dikenali. Coba: 'analisa BBCA', 'bandingkan BBCA dan BBRI', 'info'")


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
    console.print('  "[query]"            - Bahasa natural (contoh: "BBCA" atau "analisa BBCA")')
    console.print("  info                 - Bantuan ini")


if __name__ == "__main__":
    app()
