from app.tools.yahoo_finance import get_stock_data
from app.screeners.engine import screen_stock
from app.indicators.engine import sma, ema, rsi, macd, atr, bollinger, adx, stochastic
from app.models.stock import StockData
from app.screeners.engine import ScreeningResult


def fetch_stock(ticker: str) -> StockData | None:
    return get_stock_data(ticker)


def run_screening(data: StockData) -> list[ScreeningResult]:
    return screen_stock(data)


def build_context(data: StockData) -> dict:
    return {
        "ticker": data.info.ticker,
        "name": data.info.name,
        "sector": data.info.sector or "-",
        "price": data.history[-1].close if data.history else 0,
        "change": _calc_change(data),
        "indicators": _calc_indicators(data),
        "screening": _summarize_screening(data),
    }


def _calc_change(data: StockData) -> str:
    if len(data.history) < 2:
        return "0%"
    prev = data.history[-2].close
    curr = data.history[-1].close
    pct = ((curr - prev) / prev) * 100 if prev else 0
    return f"{pct:+.2f}%"


def _calc_indicators(data: StockData) -> str:
    h = data.history
    parts = []
    rsi_vals = rsi(h)
    rsi_last = next((v for v in reversed(rsi_vals) if v is not None), None)
    if rsi_last:
        parts.append(f"RSI={rsi_last:.1f}")

    macd_vals = macd(h)
    macd_last = next((v for v in reversed(macd_vals) if v is not None), None)
    if macd_last:
        parts.append(f"MACD={'bullish' if macd_last['macd'] > macd_last['signal'] else 'bearish'}")

    sma20 = sma(h, 20)
    sma20_v = next((v for v in reversed(sma20) if v is not None), None)
    if sma20_v:
        parts.append(f"SMA20={sma20_v:.0f}")

    sma50 = sma(h, 50)
    sma50_v = next((v for v in reversed(sma50) if v is not None), None)
    if sma50_v:
        parts.append(f"SMA50={sma50_v:.0f}")

    bb = bollinger(h)
    bb_last = next((v for v in reversed(bb) if v is not None), None)
    if bb_last:
        parts.append(f"BB={bb_last['upper']:.0f}/{bb_last['middle']:.0f}/{bb_last['lower']:.0f}")

    return " | ".join(parts) if parts else "Data tidak mencukupi"


def _summarize_screening(data: StockData) -> str:
    results = run_screening(data)
    if not results:
        return "Tidak ada sinyal"
    return "; ".join(f"{r.signal}: {r.reason}" for r in results)
