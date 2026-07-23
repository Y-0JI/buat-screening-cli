import math
from app.models.stock import HistoricalPrice


def _closes(prices: list[HistoricalPrice]) -> list[float]:
    return [p.close for p in prices]


def _highs(prices: list[HistoricalPrice]) -> list[float]:
    return [p.high for p in prices]


def _lows(prices: list[HistoricalPrice]) -> list[float]:
    return [p.low for p in prices]


def sma(prices: list[HistoricalPrice], period: int = 20) -> list[float | None]:
    c = _closes(prices)
    result: list[float | None] = []
    for i in range(len(c)):
        if i < period - 1:
            result.append(None)
        else:
            result.append(sum(c[i - period + 1 : i + 1]) / period)
    return result


def ema(prices: list[HistoricalPrice], period: int = 20) -> list[float | None]:
    c = _closes(prices)
    result: list[float | None] = []
    multiplier = 2 / (period + 1)
    for i in range(len(c)):
        if i < period - 1:
            result.append(None)
        elif i == period - 1:
            result.append(sum(c[: period]) / period)
        else:
            prev = result[-1]
            result.append((c[i] - prev) * multiplier + prev)
    return result


def rsi(prices: list[HistoricalPrice], period: int = 14) -> list[float | None]:
    c = _closes(prices)
    result: list[float | None] = []
    gains: list[float] = []
    losses: list[float] = []
    for i in range(len(c)):
        if i == 0:
            result.append(None)
            gains.append(0.0)
            losses.append(0.0)
        else:
            change = c[i] - c[i - 1]
            g = change if change > 0 else 0.0
            l = -change if change < 0 else 0.0
            gains.append(g)
            losses.append(l)
            if i < period:
                result.append(None)
            elif i == period:
                avg_g = sum(gains[1 : period + 1]) / period
                avg_l = sum(losses[1 : period + 1]) / period
                rs = avg_g / avg_l if avg_l != 0 else (1.0 if avg_g == 0 else 100.0)
                result.append(100.0 - (100.0 / (1.0 + rs)))
            else:
                avg_g = ((period - 1) * gains[i] + g) / period
                avg_l = ((period - 1) * losses[i] + l) / period
                gains[i] = avg_g
                losses[i] = avg_l
                rs = avg_g / avg_l if avg_l != 0 else (1.0 if avg_g == 0 else 100.0)
                result.append(100.0 - (100.0 / (1.0 + rs)))
    return result


def macd(prices: list[HistoricalPrice]) -> list[dict | None]:
    c = _closes(prices)
    ema12 = _ema_raw(c, 12)
    ema26 = _ema_raw(c, 26)
    result: list[dict | None] = []
    macd_line_values: list[float] = []
    for i in range(len(c)):
        if ema12[i] is None or ema26[i] is None:
            result.append(None)
            macd_line_values.append(0.0)
        else:
            macd_val = ema12[i] - ema26[i]
            macd_line_values.append(macd_val)
            if len(macd_line_values) < 10:
                result.append(None)
            else:
                signal = sum(macd_line_values[-9:]) / 9
                result.append({"macd": round(macd_val, 4), "signal": round(signal, 4), "histogram": round(macd_val - signal, 4)})
    return result


def _ema_raw(values: list[float], period: int) -> list[float | None]:
    result: list[float | None] = []
    multiplier = 2 / (period + 1)
    for i in range(len(values)):
        if i < period - 1:
            result.append(None)
        elif i == period - 1:
            result.append(sum(values[:period]) / period)
        else:
            prev = result[-1]
            result.append((values[i] - prev) * multiplier + prev)
    return result


def atr(prices: list[HistoricalPrice], period: int = 14) -> list[float | None]:
    result: list[float | None] = []
    tr_values: list[float] = []
    for i in range(len(prices)):
        if i == 0:
            tr = prices[i].high - prices[i].low
        else:
            hl = prices[i].high - prices[i].low
            hc = abs(prices[i].high - prices[i - 1].close)
            lc = abs(prices[i].low - prices[i - 1].close)
            tr = max(hl, hc, lc)
        tr_values.append(tr)
        if i < period:
            result.append(None)
        elif i == period:
            result.append(sum(tr_values[: period]) / period)
        else:
            prev = result[-1]
            result.append((prev * (period - 1) + tr) / period)
    return result


def bollinger(prices: list[HistoricalPrice], period: int = 20) -> list[dict | None]:
    c = _closes(prices)
    result: list[dict | None] = []
    for i in range(len(c)):
        if i < period - 1:
            result.append(None)
        else:
            window = c[i - period + 1 : i + 1]
            mean = sum(window) / period
            variance = sum((x - mean) ** 2 for x in window) / period
            std = math.sqrt(variance)
            result.append({
                "middle": round(mean, 2),
                "upper": round(mean + 2 * std, 2),
                "lower": round(mean - 2 * std, 2),
            })
    return result


def adx(prices: list[HistoricalPrice], period: int = 14) -> list[float | None]:
    result: list[float | None] = []
    plus_dm: list[float] = []
    minus_dm: list[float] = []
    tr_values: list[float] = []
    atr_values: list[float] = []
    plus_di: list[float] = []
    minus_di: list[float] = []
    dx_values: list[float] = []

    for i in range(len(prices)):
        if i == 0:
            tr = prices[i].high - prices[i].low
            plus_dm.append(0.0)
            minus_dm.append(0.0)
        else:
            hl = prices[i].high - prices[i].low
            hc = abs(prices[i].high - prices[i - 1].close)
            lc = abs(prices[i].low - prices[i - 1].close)
            tr = max(hl, hc, lc)
            up_move = prices[i].high - prices[i - 1].high
            down_move = prices[i - 1].low - prices[i].low
            if up_move > down_move and up_move > 0:
                plus_dm.append(up_move)
            else:
                plus_dm.append(0.0)
            if down_move > up_move and down_move > 0:
                minus_dm.append(down_move)
            else:
                minus_dm.append(0.0)

        tr_values.append(tr)

        if i < period:
            result.append(None)
            plus_di.append(0.0)
            minus_di.append(0.0)
            atr_values.append(0.0)
            dx_values.append(0.0)
        elif i == period:
            atr_val = sum(tr_values[: period]) / period
            sum_plus = sum(plus_dm[: period])
            sum_minus = sum(minus_dm[: period])
            atr_values.append(atr_val)
            pdi = 100.0 * sum_plus / atr_val if atr_val != 0 else 0.0
            mdi = 100.0 * sum_minus / atr_val if atr_val != 0 else 0.0
            plus_di.append(pdi)
            minus_di.append(mdi)
            dx = abs(pdi - mdi) / (pdi + mdi) * 100 if (pdi + mdi) != 0 else 0.0
            dx_values.append(dx)
            result.append(dx)
        else:
            atr_val = (atr_values[-1] * (period - 1) + tr) / period
            sum_plus = plus_dm[i] * (period - 1) / period + (plus_dm[i]) if i == period + 1 else (plus_di[-1] * (period - 1) + plus_dm[i]) / period
            sum_minus = minus_dm[i] * (period - 1) / period + (minus_dm[i]) if i == period + 1 else (minus_di[-1] * (period - 1) + minus_dm[i]) / period
            atr_values.append(atr_val)
            pdi = 100.0 * sum_plus / atr_val if atr_val != 0 else 0.0
            mdi = 100.0 * sum_minus / atr_val if atr_val != 0 else 0.0
            plus_di.append(pdi)
            minus_di.append(mdi)
            dx = abs(pdi - mdi) / (pdi + mdi) * 100 if (pdi + mdi) != 0 else 0.0
            dx_values.append(dx)
            if i < period * 2 - 1:
                result.append(None)
            else:
                adx_val = sum(dx_values[i - period + 1: i + 1]) / period
                result.append(adx_val)
    return result


def stochastic(prices: list[HistoricalPrice], period: int = 14) -> list[dict | None]:
    result: list[dict | None] = []
    fast_k_values: list[float] = []
    for i in range(len(prices)):
        if i < period - 1:
            result.append(None)
        else:
            window_high = max(p.high for p in prices[i - period + 1 : i + 1])
            window_low = min(p.low for p in prices[i - period + 1 : i + 1])
            if window_high == window_low:
                fast_k = 50.0
            else:
                fast_k = (prices[i].close - window_low) / (window_high - window_low) * 100
            fast_k_values.append(fast_k)
            if len(fast_k_values) < 3:
                result.append({"k": round(fast_k, 2), "d": None})
            else:
                slow_d = sum(fast_k_values[-3:]) / 3
                result.append({"k": round(fast_k, 2), "d": round(slow_d, 2)})
    return result
