from app.agent.core import analyze_with_ai, compare_with_ai, ask_llm
from app.agent.research import run_research
from app.router.engine import fetch_stock, build_context, run_screening, bulk_screen, bulk_gainers, bulk_losers
from app.services.stock_list import get_all, search
from app.models.analysis import AIAnalysis
from app.models.stock import StockData
from app.screeners.engine import ScreeningResult


def analyze_stock(ticker: str) -> AIAnalysis:
    return analyze_with_ai(ticker)


def compare_stocks(tickers: list[str]) -> dict:
    return compare_with_ai(tickers)


def ask_question(query: str, context: str = "") -> str | None:
    return ask_llm(query, context)


def run_research_query(query: str):
    return run_research(query)


def screen_stocks(sector: str | None = None, limit: int = 10) -> list[dict]:
    tickers = [s["ticker"] for s in get_all()]
    results = bulk_screen(tickers)
    if sector:
        results = [r for r in results if r.get("sector") and sector.lower() in r["sector"].lower()]
    if limit:
        results = results[:limit]
    return results


def get_trend(ticker: str) -> dict | None:
    data = fetch_stock(ticker)
    if not data:
        return None
    ctx = build_context(data)
    return {
        "ticker": data.info.ticker,
        "name": data.info.name,
        "sector": data.info.sector,
        "price": ctx["price"],
        "change": ctx["change"],
        "indicators": ctx["indicators"],
        "screening": ctx["screening"],
    }


def get_score(ticker: str) -> list[ScreeningResult] | None:
    data = fetch_stock(ticker)
    if not data:
        return None
    return run_screening(data)


def list_stocks(query: str | None = None) -> list[dict]:
    return search(query) if query else get_all()


def fetch_stock_data(ticker: str) -> StockData | None:
    return fetch_stock(ticker)
