from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.agent.core import analyze_with_ai
from app.agent.enrichment import enrich_financials
from app.router.engine import build_context, fetch_stock, run_screening
from app.tools import get_provider
from app.validation import normalize


@dataclass
class CompositeBlock:
    status: str
    data: dict = field(default_factory=dict)
    error: str | None = None


@dataclass
class CompositeResult:
    ticker: str
    name: str
    blocks: dict[str, CompositeBlock] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


def _ok(data: dict) -> CompositeBlock:
    return CompositeBlock(status="available", data=data)


def _fail(error: str) -> CompositeBlock:
    return CompositeBlock(status="unavailable", data={}, error=error)


def _partial(data: dict, error: str) -> CompositeBlock:
    return CompositeBlock(status="partial", data=data, error=error)


provider = get_provider()


def _merge_first_wins(dst: dict, src: dict) -> None:
    """Merge src ke dst leaf-by-leaf; key yang sudah ada menang."""
    for k, v in src.items():
        if isinstance(v, dict):
            dst.setdefault(k, {})
            _merge_first_wins(dst[k], v)
        elif k not in dst:
            dst[k] = v


def build_composite(ticker: str) -> CompositeResult:
    t = normalize(ticker)
    result = CompositeResult(ticker=t, name="")
    data = fetch_stock(t)
    if not data:
        err = "Data tidak ditemukan"
        for block in ("quote", "stats", "signal", "narrative"):
            result.blocks[block] = _fail(err)
        return result

    ctx = build_context(data)
    result.name = ctx["name"]
    result.blocks["quote"] = _ok({
        "price": ctx["price"],
        "change": ctx["change"],
        "name": ctx["name"],
        "sector": ctx["sector"],
    })

    signals = [{
        "signal": s.signal,
        "reason": s.reason,
        "confidence": s.confidence,
    } for s in run_screening(data)]
    result.blocks["signal"] = _ok({"signals": signals})

    stats: dict = {"indicators": ctx["indicators"]}

    def _narrative() -> None:
        try:
            a = analyze_with_ai(t)
            result.blocks["narrative"] = _ok({"summary": a.summary})
        except Exception as e:
            result.blocks["narrative"] = _fail(str(e))

    def _financials() -> None:
        try:
            raw = provider.fetch_financials(t)
            if raw:
                ratio = enrich_financials(raw, ctx["price"], data.info.fundamentals)
                _merge_first_wins(stats, ratio)
            result.blocks["stats"] = _ok(stats)
        except Exception as e:
            result.blocks["stats"] = _partial(stats, str(e))

    with ThreadPoolExecutor(max_workers=2) as ex:
        f1 = ex.submit(_narrative)
        f2 = ex.submit(_financials)
        f1.result()
        f2.result()

    if "stats" not in result.blocks:
        result.blocks["stats"] = _ok(stats)
    return result