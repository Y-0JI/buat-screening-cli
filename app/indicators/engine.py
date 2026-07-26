import math
from app.models.stock import HistoricalPrice


def _closes(prices: list[HistoricalPrice]) -> list[float]:
    return [p.close for p in prices]


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
                gains[i] = avg_g
                losses[i] = avg_l
                rs = avg_g / avg_l if avg_l != 0 else (1.0 if avg_g == 0 else 100.0)
                result.append(100.0 - (100.0 / (1.0 + rs)))
            else:
                avg_g = ((period - 1) * gains[i - 1] + g) / period
                avg_l = ((period - 1) * losses[i - 1] + l) / period
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

