import math
from statistics import stdev

from app.indicators.engine import sma
from app.models.research import SectionStatus
from app.models.stock import HistoricalPrice

# Confidence algorithm (deterministic, auditable):
# - weights: available=1.0, partial=0.5, missing=0.0 (equal across relevant sections)
# - intent-aware: sections irrelevant to the research type are excluded from the
#   denominator (e.g. market context for single-stock research)
# - score = sum(weights) / count(relevant); high >= 0.8, medium >= 0.5, low < 0.5
_SECTION_WEIGHTS = {
    SectionStatus.AVAILABLE: 1.0,
    SectionStatus.PARTIAL: 0.5,
    SectionStatus.MISSING: 0.0,
}
_HIGH_THRESHOLD = 0.8
_MEDIUM_THRESHOLD = 0.5

_INTENT_RELEVANT_SECTIONS = {
    "single_stock": ("company", "price", "technical", "risk", "fundamental", "financial", "valuation", "growth", "dividend", "market_intelligence"),
    "analyze_only": ("company", "price", "technical", "risk", "fundamental", "financial", "valuation", "growth", "dividend", "market_intelligence"),
    "sector_theme": ("market", "company", "price", "technical", "risk", "fundamental", "financial", "valuation", "growth", "dividend", "market_intelligence"),
    "comparative": ("company", "price", "technical", "comparison", "risk", "fundamental", "financial", "valuation", "growth", "dividend", "market_intelligence"),
}


def compute_confidence(intent_type: str, sections: dict) -> dict:
    """Confidence = data completeness/quality, NOT recommendation strength.
    Returns score, level, per-section breakdown and score reducers."""
    keys = _INTENT_RELEVANT_SECTIONS.get(intent_type, ())
    breakdown = {}
    weighted = 0.0
    for key in keys:
        sec = sections[key]
        weight = _SECTION_WEIGHTS.get(sec.status, 0.0)
        weighted += weight
        breakdown[key] = {"status": sec.status.value, "weight": weight, "reason": sec.reason}
    score = round(weighted / len(keys), 2) if keys else 0.0
    level = "high" if score >= _HIGH_THRESHOLD else "medium" if score >= _MEDIUM_THRESHOLD else "low"
    return {
        "confidence_level": level,
        "confidence_score": score,
        "confidence_breakdown": breakdown,
        "missing_sections": {k: v["reason"] for k, v in breakdown.items() if v["status"] == "missing"},
        "partial_sections": {k: v["reason"] for k, v in breakdown.items() if v["status"] == "partial"},
    }


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


def compute_technical_context(history: list[HistoricalPrice], week52_change_pct: float | None) -> dict:
    """Technical numbers only (no sentiment labels) — interpretation is the AI's job."""
    close = history[-1].close
    out = {"price": round(close, 2)}
    for period, key in ((20, "vs_sma20_pct"), (50, "vs_sma50_pct")):
        vals = [v for v in sma(history, period) if v is not None]
        if vals:
            out[key] = round((close - vals[-1]) / vals[-1] * 100, 2)
    if week52_change_pct is not None:
        out["week52_change_pct"] = round(week52_change_pct * 100, 2)
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


def _ratio(numerator: float | None, denominator) -> float | None:
    if numerator is None or not denominator:
        return None
    return round(numerator / denominator, 4)


def enrich_financials(raw: dict, price: float | None = None, info_fundamentals: dict | None = None) -> dict:
    """Financial statements -> normalized metrics. Deterministic, no raw data kept.

    Extra per-share basis (Diluted EPS, Book Value) may arrive in a dedicated
    `derived` leaf (IDX IDR scale). Ratios that need a currency-consistent
    price/eps only when authoritative info fields are missing.
    """
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

    net_income = (out.get("net_income") or {}).get("latest")
    revenue = (out.get("revenue") or {}).get("latest")
    latest_equity = (out.get("equity") or {}).get("latest")
    der = _ratio(_latest(_series(bs, "Total Liabilities")), latest_equity)
    if der is not None:
        out["der"] = der
    roa = _ratio(net_income, _latest(_series(bs, "Total Assets")))
    if roa is not None:
        out["roa"] = roa
    roe = _ratio(net_income, latest_equity)
    if roe is not None:
        out["roe"] = roe
    npm = _ratio(net_income, revenue)
    if npm is not None:
        out["npm"] = npm

    derived = raw.get("derived", {})
    eps = _latest(_series(derived, "EPS"))
    if eps is None:
        eps = _latest(_series(fin, "Diluted EPS"))
    if eps is None:
        eps = _latest(_series(fin, "Basic EPS"))
    per = _per_guard(price, eps, info_fundamentals)
    if per is not None:
        out["per"] = per
    book = _latest(_series(derived, "Book Value"))
    if book and price:
        out["pbv"] = _ratio(price, book)
    elif book is None:
        info_pb = (info_fundamentals or {}).get("priceToBook")
        if info_pb is not None and 0 < info_pb <= 200:  # semoga bukan garbage unit 14470
            out["pbv"] = round(info_pb, 4)
    return out


def _per_guard(price: float | None, eps: float | None, info_fundamentals: dict | None) -> float | None:
    """PER with cross-currency guard.

    Yahoo raw EPS is USD-scale while price is IDR — price/eps from raw can be
    148k garbage (e.g. ADRO). An authoritative trailingPE in `.info` always
    wins; raw computation is best-effort only when it is absent.
    """
    info_pe = (info_fundamentals or {}).get("trailingPE")
    if info_pe is not None and info_pe > 0:
        return round(info_pe, 4)
    if eps is None or eps <= 0 or not price or price <= 0:
        return None
    return round(price / eps, 4)
