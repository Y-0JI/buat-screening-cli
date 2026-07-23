import typer
from typing import Optional
from app.config.settings import settings
from app.utils.logging import setup_logging
from app.parser.intent import parse
from app.agent.core import analyze_with_ai, compare_with_ai, ask_llm
from app.cli.formatter import print_ai_analysis, print_error, print_info, console
from app.router.engine import fetch_stock, build_context, run_screening
from app.cli.formatter import print_stock_header, print_screening_results

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
def screen() -> None:
    print_info("Fitur screen penuh akan menggunakan data dari daftar saham IDX")


@app.command()
def natural(query: str) -> None:
    from app.parser.intent import parse
    intent, params = parse(query)
    if intent == "analyze":
        analyze(params.get("ticker", ""))
    elif intent == "compare":
        tk = params.get("tickers", "")
        compare(tk)
    elif intent == "screen":
        screen()
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
    console.print('  natural "[query]"    - Bahasa natural')
    console.print("  info                 - Bantuan ini")


if __name__ == "__main__":
    app()
