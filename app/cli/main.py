import typer
from app.config.settings import settings
from app.utils.logging import setup_logging
from app.parser.intent import parse
from app.agent.core import process, ask_llm
from app.cli.formatter import print_stock_header, print_price_info, print_screening_results, print_error, print_info, console

app = typer.Typer()


@app.callback()
def main() -> None:
    setup_logging(settings.log_level)


@app.command()
def analyze(ticker: str) -> None:
    result = process("analyze", {"ticker": ticker})
    data = result.get("data")
    if not data:
        print_error(f"Data untuk {ticker.upper()} tidak ditemukan")
        raise typer.Exit(1)
    print_stock_header(data)
    print_price_info(data)


@app.command()
def screen() -> None:
    print_info("Fitur screen penuh akan menggunakan data dari daftar saham IDX")


@app.command()
def compare(tickers: str) -> None:
    result = process("compare", {"tickers": tickers.upper()})
    for r in result.get("results", []):
        data = r.get("data")
        if data:
            print_stock_header(data)
            print_price_info(data)
        else:
            print_error(f"Data untuk {r['ticker']} tidak ditemukan")


@app.command()
def natural(query: str) -> None:
    intent, params = parse(query)
    if intent in ("analyze", "compare", "screen", "help"):
        result = process(intent, params)
        intent_type = result.get("type")

        if intent_type == "analyze":
            data = result.get("data")
            if data:
                print_stock_header(data)
                print_price_info(data)
            else:
                print_error(f"Data untuk {params.get('ticker', '?')} tidak ditemukan")
        elif intent_type == "compare":
            for r in result.get("results", []):
                data = r.get("data")
                if data:
                    print_stock_header(data)
                    print_price_info(data)
        elif intent_type == "screen":
            screen()
        elif intent_type == "help":
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
    console.print("  analyze [ticker]     - Analisa saham")
    console.print("  screen               - Screening saham")
    console.print("  compare [t1,t2]      - Bandingkan dua saham")
    console.print('  natural "[query]"    - Bahasa natural')
    console.print("  info                 - Bantuan ini")


if __name__ == "__main__":
    app()
