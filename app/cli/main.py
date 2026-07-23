import typer
from app.config.settings import settings
from app.utils.logging import setup_logging
from app.cli.formatter import print_error, print_info
from app.agent.parser import parse_intent, INTENT_ANALYZE, INTENT_SCREEN, INTENT_COMPARE, INTENT_HELP

app = typer.Typer()


@app.callback()
def main() -> None:
    setup_logging(settings.log_level)


@app.command()
def analyze(ticker: str) -> None:
    from app.tools.yahoo_finance import get_stock_data
    from app.cli.formatter import print_stock_header, print_price_info
    data = get_stock_data(ticker)
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
    from app.tools.yahoo_finance import get_stock_data
    from app.cli.formatter import print_stock_header, print_price_info
    parts = [t.strip().upper() for t in tickers.split(",")]
    for t in parts:
        data = get_stock_data(t)
        if data:
            print_stock_header(data)
            print_price_info(data)
        else:
            print_error(f"Data untuk {t} tidak ditemukan")


@app.command()
def natural(query: str) -> None:
    intent, params = parse_intent(query)
    if intent == INTENT_ANALYZE:
        from app.tools.yahoo_finance import get_stock_data
        from app.cli.formatter import print_stock_header, print_price_info
        data = get_stock_data(params["ticker"])
        if not data:
            print_error(f"Data untuk {params['ticker']} tidak ditemukan")
            return
        print_stock_header(data)
        print_price_info(data)
    elif intent == INTENT_SCREEN:
        print_info(f"Screening: {params.get('type', 'all')}")
    elif intent == INTENT_COMPARE:
        from app.tools.yahoo_finance import get_stock_data
        from app.cli.formatter import print_stock_header, print_price_info
        for t in params["tickers"].split(","):
            t = t.strip()
            data = get_stock_data(t)
            if data:
                print_stock_header(data)
                print_price_info(data)
    elif intent == INTENT_HELP:
        from app.cli.formatter import console
        console.print("[bold]Screening CLI[/bold] - AI-powered Indonesian stock screener")
        console.print("Commands: analyze, screen, compare, natural, info")
    else:
        from app.agent.core import ask_agent
        resp = ask_agent(query)
        if resp:
            from app.cli.formatter import console
            console.print(resp)
        else:
            print_error("Query tidak dikenali. Coba: 'analisa BBCA', 'bandingkan BBCA dan BBRI', 'help'")


@app.command()
def info() -> None:
    from app.cli.formatter import console
    console.print("[bold]Available commands:[/bold]")
    console.print("  analyze [ticker]     - Analisa saham")
    console.print("  screen               - Screening saham")
    console.print("  compare [t1,t2]      - Bandingkan dua saham")
    console.print('  natural "[query]"    - Bahasa natural')
    console.print("  info (help)          - Bantuan ini")


if __name__ == "__main__":
    app()
