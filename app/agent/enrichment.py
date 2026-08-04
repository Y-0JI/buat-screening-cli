import math
from statistics import stdev


def compute_volatility(closes: list[float], window: int = 30) -> float | None:
    """Annualized volatility (%) from daily close returns. Deterministic."""
    if len(closes) < window + 2:
        window = len(closes) - 1
        if window < 2:
            return None
    recent = closes[-window - 1 :]
    returns = [(recent[i + 1] - recent[i]) / recent[i] for i in range(len(recent) - 1)]
    if len(returns) < 2:
        return None
    return round(stdev(returns) * math.sqrt(252) * 100, 2)


def compute_price_position(price: float, week52_high: float | None, week52_low: float | None) -> dict:
    out = {}
    if week52_high:
        out["week52_high"] = week52_high
        out["pct_from_high"] = round((price - week52_high) / week52_high * 100, 2)
    if week52_low:
        out["week52_low"] = week52_low
        out["pct_from_low"] = round((price - week52_low) / week52_low * 100, 2)
    return out


def _series(rows: dict, label: str) -> list[tuple[str, float]]:
    periods = []
    for period, values in rows.items():
        for key, val in values.items():
            if label.lower() in str(key).lower() and isinstance(val, (int, float)):
                periods.append((str(period), val))
    periods.sort(reverse=True)
    return periods


def _trend(values: list[float]) -> dict:
    if not values:
        return {}
    latest = round(values[0], 2)
    out = {"latest": latest}
    if len(values) > 1 and values[1]:
        out["yoy_pct"] = round((latest - values[1]) / abs(values[1]) * 100, 1)
    return out


def _latest(values: list[tuple[str, float]]) -> float | None:
    return round(values[0][1], 2) if values else None


def enrich_financials(raw: dict) -> dict:
    """Financial statements -> normalized metrics. Deterministic, no raw data kept."""
    out = {}
    fin = raw.get("financials", {})
    rev = [v for _, v in _series(fin, "Total Revenue")][:3]
    if rev:
        out["revenue"] = _trend(rev)
    ni = [v for _, v in _series(fin, "Net Income Common Stockholders")][:3]
    if ni:
        out["net_income"] = _trend(ni)

    bs = raw.get("balance_sheet", {})
    debt = [v for _, v in _series(bs, "Total Debt")][:2]
    if debt:
        out["total_debt"] = _trend(debt)
    cash = [v for _, v in _series(bs, "Cash And Cash Equivalents")][:2]
    if cash:
        out["cash"] = _trend(cash)
    equity = [v for _, v in _series(bs, "Stockholders Equity")][:2]
    if equity:
        out["equity"] = _trend(equity)

    cf = raw.get("cashflow", {})
    ocf = _latest(_series(cf, "Operating Cash Flow"))
    if ocf is not None:
        out["operating_cash_flow"] = {"latest": ocf}
    fcf = _latest(_series(cf, "Free Cash Flow"))
    if fcf is not None:
        out["free_cash_flow"] = {"latest": fcf}
    return out
