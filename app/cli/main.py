import sys
import typer
from app.config.settings import settings
from app.utils.logging import setup_logging
from app.engine.capabilities import analyze_stock, compare_stocks, run_research_query, ask_question
from app.engine.capabilities import get_trend, get_score, screen_stocks, list_stocks
from app.engine.capabilities import fetch_stock_data
from app.cli.formatter import console, print_ai_analysis, print_error, print_info
from app.cli.formatter import print_research_report, print_stock_header
from app.cli.formatter import print_screening_results, print_bulk_screening, print_gainer_loser_table
from app.parser.intent import INTENT_UNKNOWN, INTENT_RESEARCH, parse
from typing import Optional

_KNOWN_COMMANDS = {"analyze", "trend", "score", "compare", "screen", "gainers",
                   "losers", "sector", "stocks", "natural", "info", "chat", "research"}

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
    with console.status(f"[bold blue]Menganalisis {ticker.upper()}..."):
        result = analyze_stock(ticker)
    print_ai_analysis(result)


@app.command()
def trend(ticker: str) -> None:
    ctx = get_trend(ticker)
    if not ctx:
        print_error(f"Data untuk {ticker.upper()} tidak ditemukan")
        raise typer.Exit(1)
    print_stock_header(fetch_stock_data(ticker))
    info_text = f"Indikator: {ctx['indicators']}\nScreening: {ctx['screening']}"
    console.print(f"[bold]Info Teknikal:[/bold]\n{info_text}")


@app.command()
def score(ticker: str) -> None:
    data = fetch_stock_data(ticker)
    if not data:
        print_error(f"Data untuk {ticker.upper()} tidak ditemukan")
        raise typer.Exit(1)
    results = get_score(ticker)
    print_stock_header(data)
    if results:
        print_screening_results(results)
    else:
        print_info("Tidak ada sinyal screening ditemukan")


@app.command()
def compare(
    ticker1: str = typer.Argument(help="Ticker pertama (atau dua ticker pisah koma)"),
    ticker2: str = typer.Argument("", help="Ticker kedua (opsional)"),
) -> None:
    tickers_str = f"{ticker1},{ticker2}" if ticker2 else ticker1
    tickers = [t.strip().upper() for t in tickers_str.replace(",", " ").split()]
    with console.status(f"[bold blue]Membandingkan {', '.join(tickers)}..."):
        result = compare_stocks(tickers)
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
    with console.status(f"[bold blue]Screening saham..."):
        results = screen_stocks(sector, limit)
    if not results:
        print_info("Tidak ada sinyal screening ditemukan")
        return
    title = f"Hasil Screening{' — ' + sector if sector else ''}"
    print_bulk_screening(results, title=title)


@app.command()
def gainers(limit: int = 10) -> None:
    from app.router.engine import bulk_gainers
    from app.services.stock_list import get_all
    tickers = [s["ticker"] for s in get_all()]
    with console.status(f"[bold blue]Mengambil harga {len(tickers)} saham..."):
        results = bulk_gainers(tickers)
    print_gainer_loser_table(results[:limit], title="Top Gainers")


@app.command()
def losers(limit: int = 10) -> None:
    from app.router.engine import bulk_losers
    from app.services.stock_list import get_all
    tickers = [s["ticker"] for s in get_all()]
    with console.status(f"[bold blue]Mengambil harga {len(tickers)} saham..."):
        results = bulk_losers(tickers)
    print_gainer_loser_table(results[:limit], title="Top Losers")


@app.command()
def sector(name: str = typer.Argument(help="Nama sektor, contoh: Financials")) -> None:
    with console.status(f"[bold blue]Screening {len(name)} saham sektor {name}..."):
        results = screen_stocks(name)
    if not results:
        print_info(f"Tidak ada sinyal screening di sektor {name}")
        return
    print_bulk_screening(results, title=f"Hasil Screening — {name}")


@app.command()
def stocks(query: Optional[str] = typer.Argument(None, help="Cari kode/nama saham")) -> None:
    all_stocks = list_stocks(query)
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
        resp = ask_question(query)
        if resp:
            console.print(resp)
        else:
            print_error("Query tidak dikenali. Coba: 'analisa BBCA', 'bandingkan BBCA dan BBRI', 'info'")


@app.command()
def research(query: str) -> None:
    with console.status(f"[bold blue]Menjalankan riset untuk: {query}..."):
        report = run_research_query(query)
    print_research_report(report)


@app.command()
def chat() -> None:
    console.print("[bold]Mode diskusi. Ketik 'exit' atau Ctrl-C untuk keluar.[/bold]")
    history: list[str] = []
    while True:
        try:
            query = console.input("[bold cyan]>> [/bold cyan]")
            if query.lower() in ("exit", "quit", "keluar"):
                break
            context = "\n".join(history[-6:]) if history else ""
            resp = ask_question(query, context)
            if resp:
                console.print(resp)
                history.append(f"User: {query}")
                history.append(f"AI: {resp}")
            else:
                print_error("AI tidak merespon. Periksa konfigurasi .env")
        except (EOFError, KeyboardInterrupt):
            console.print()
            break


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
    console.print("  info                 - Bantuan ini")


if __name__ == "__main__":
    app()