"""Koordinasi Phase 2 — routing workflow, orchestration multi-klausa, follow-up 1-hop.

Semua keputusan workflow ada di lapisan ini; parser tetap pure (hanya data).
Helper di sini murni (input -> output), tanpa I/O storage/network.
"""

import re
from dataclasses import dataclass

from app.parser.ambiguity import CLAUSE_SEPARATORS
from app.parser.intent import ParseResult, parse
from app.validation import normalize

RESEARCH_QUALIFIERS = ("fundamental", "teknikal", "lengkap", "riset", "research", "laporan")


@dataclass
class ExecutionContext:
    """Data carrier ringan untuk pipeline koordinasi. Hanya data — logger,
    storage, service, client TIDAK dimasukkan ke sini (anti God Object).
    Phase 3 bisa menambah session/conversation tanpa ubah signature."""

    query: str
    parse_result: ParseResult
    last_context: str | None = None
    workflow: str | None = None


def split_clauses(query: str) -> list[str]:
    """Split query jadi klausa — SATU-SATUNYA sumber pemisahan klausa
    (pakai CLAUSE_SEPARATORS yang sama dengan parser). Kalau separator
    perlu ditambah, cukup di satu tempat ini."""
    return [c.strip() for c in re.split(CLAUSE_SEPARATORS, query) if c.strip()]


def route_intent(result: ParseResult, query: str) -> str:
    """Pilih workflow dari intent. ANALYZE polos tetap analyze cepat;
    ANALYZE + qualifier riset eksplisit -> research penuh. Intent lain -> dirinya."""
    if result.intent == "analyze":
        q = query.lower()
        if any(qual in q for qual in RESEARCH_QUALIFIERS):
            return "research"
    if result.intent == "unknown" and re.match(r"^(?:laporan|report)\s+\w{2,5}$", query.strip().lower()):
        return "research"
    return result.intent


_FOLLOWUP_COMPARE = re.compile(r"^(?:bandingkan\s+dengan|bandingkan|vs\.?|versus)\s+(\w{2,5})$", re.IGNORECASE)


def resolve_followup(query: str, parse_result: ParseResult, last_context: str | None) -> str | None:
    """Pure 1-hop follow-up: lengkapi query pendek dengan ticker dari last_context.
    Tidak menyentuh memory/storage — pemanggil yang ambil & pass last_context.
    Tanpa konteks / pola tak cocok -> None (query jalan seperti biasa)."""
    if not last_context:
        return None
    ctx_ticker = _extract_context_ticker(last_context)
    if not ctx_ticker:
        return None
    m = _FOLLOWUP_COMPARE.match(query.strip())
    if m:
        other = normalize(m.group(1))
        return f"bandingkan {ctx_ticker} dan {other}"
    if parse_result.intent == "compare":
        tickers = [t for t in parse_result.params.get("tickers", "").replace(",", " ").split() if t]
        if len(tickers) == 1:
            return f"bandingkan {ctx_ticker} dan {tickers[0]}"
    return None


def _extract_context_ticker(last_context: str) -> str | None:
    """Ticker dari entri RESEARCH_FINDING terakhir — query asli ada di dalam
    single quotes ('analisa BBCA'), di-parse ulang pakai parser yang sama."""
    m = re.search(r"'([^']*?)'", last_context)
    if not m:
        return None
    _, params = parse(m.group(1))
    if params.get("ticker"):
        return params["ticker"]
    tickers = params.get("tickers", "")
    if tickers:
        return tickers.replace(",", " ").split()[0]
    return None
