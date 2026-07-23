from dataclasses import dataclass
from app.models.stock import StockData
from app.indicators.engine import sma, ema, rsi, bollinger


@dataclass
class ScreeningResult:
    ticker: str
    signal: str
    reason: str
    confidence: float  # 0.0 to 1.0


def golden_cross(data: StockData) -> ScreeningResult | None:
    sma50 = sma(data.history, period=50)
    sma200 = sma(data.history, period=200)
    valid = [i for i in range(len(sma50)) if sma50[i] is not None and sma200[i] is not None]
    if len(valid) < 2:
        return None
    prev = valid[-2]
    curr = valid[-1]
    prev_cross = sma50[prev] is not None and sma200[prev] is not None and sma50[prev] < sma200[prev]
    curr_cross = sma50[curr] is not None and sma200[curr] is not None and sma50[curr] > sma200[curr]
    if prev_cross and curr_cross:
        return ScreeningResult(ticker=data.info.ticker, signal="BUY", reason="Golden Cross", confidence=0.8)
    return None


def rsi_signal(data: StockData) -> ScreeningResult | None:
    rsi_vals = rsi(data.history, period=14)
    valid = [v for v in rsi_vals if v is not None]
    if not valid:
        return None
    last = valid[-1]
    if last < 30:
        return ScreeningResult(ticker=data.info.ticker, signal="BUY", reason=f"RSI Oversold ({last:.1f})", confidence=0.7)
    if last > 70:
        return ScreeningResult(ticker=data.info.ticker, signal="SELL", reason=f"RSI Overbought ({last:.1f})", confidence=0.7)
    return None


def volume_spike(data: StockData, multiplier: float = 2.0) -> ScreeningResult | None:
    hist = data.history
    if len(hist) < 21:
        return None
    recent = hist[-1].volume
    avg = sum(p.volume for p in hist[-21:-1]) / 20
    if avg == 0:
        return None
    if recent / avg >= multiplier:
        return ScreeningResult(ticker=data.info.ticker, signal="WATCH", reason=f"Volume Spike ({recent/avg:.1f}x avg)", confidence=0.6)
    return None


def ema_rules(data: StockData) -> list[ScreeningResult]:
    results: list[ScreeningResult] = []
    hist = data.history
    ema20 = ema(hist, period=20)
    ema50 = ema(hist, period=50)
    close = hist[-1].close
    e20 = next((v for v in reversed(ema20) if v is not None), None)
    e50 = next((v for v in reversed(ema50) if v is not None), None)
    if e20 and close > e20:
        results.append(ScreeningResult(ticker=data.info.ticker, signal="BUY", reason=f"Price above EMA20 ({e20:.0f})", confidence=0.5))
    if e50 and close > e50:
        results.append(ScreeningResult(ticker=data.info.ticker, signal="BUY", reason=f"Price above EMA50 ({e50:.0f})", confidence=0.5))
    if e20 and e50 and e20 > e50:
        results.append(ScreeningResult(ticker=data.info.ticker, signal="BUY", reason="EMA20 above EMA50 (bullish)", confidence=0.6))
    return results


def screen_stock(data: StockData) -> list[ScreeningResult]:
    results: list[ScreeningResult] = []
    gc = golden_cross(data)
    if gc:
        results.append(gc)
    rs = rsi_signal(data)
    if rs:
        results.append(rs)
    vs = volume_spike(data)
    if vs:
        results.append(vs)
    results.extend(ema_rules(data))
    return results
