"""Koordinasi Phase 2 — routing workflow, orchestration multi-klausa, follow-up 1-hop.

Semua keputusan workflow ada di lapisan ini; parser tetap pure (hanya data).
Helper di sini murni (input -> output), tanpa I/O storage/network.
"""

import re
from dataclasses import dataclass

from app.parser.ambiguity import split_clauses
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


def resolve_followup(query: str, parse_result: ParseResult, last_context: str | None, last_source: str | None = None, universe=None) -> str | None:
    """Pure 1-hop follow-up: lengkapi query pendek dengan ticker dari konteks terakhir.
    Ticker konteks diambil dari `last_source` (ticker polos / compare: / research:),
    fallback parse content. `universe` (data murni, di-inject seperti parser) dipakai
    kanonikali ticker query yang pendek ("bri" -> BBRI, pola suffix-match ambiguity).
    Tidak menyentuh memory/storage — pemanggil yang ambil & pass konteks.
    Tanpa konteks / pola tak cocok -> None (query jalan seperti biasa)."""
    if not last_context:
        return None
    ctx_ticker = _extract_context_ticker(last_context, last_source)
    if not ctx_ticker:
        return None
    m = _FOLLOWUP_COMPARE.match(query.strip())
    if m:
        return f"bandingkan {ctx_ticker} dan {_canonical_ticker(m.group(1), universe)}"
    if parse_result.intent == "compare":
        tickers = [t for t in parse_result.params.get("tickers", "").replace(",", " ").split() if t]
        if len(tickers) == 1:
            return f"bandingkan {ctx_ticker} dan {_canonical_ticker(tickers[0], universe)}"
    return None


def _canonical_ticker(raw: str, universe) -> str:
    """Kanonikali ticker pendek via universe: exact match atau suffix-match
    ("bri" -> BBRI), pola toleran yang sama dengan ambiguity.py. Tanpa universe
    -> raw hasil normalize."""
    t = normalize(raw)
    if universe:
        for s in universe:
            tk = normalize(s["ticker"])
            if tk == t or tk.endswith(t):
                return tk
    return t


_CONTEXT_TICKER_SOURCE = re.compile(r"^[A-Z0-9.]{1,10}$")


def _extract_context_ticker(content: str, source: str | None) -> str | None:
    """Ticker dari entri RESEARCH_FINDING terakhir, prioritas source field
    (tidak bergantung format content):
    - source ticker polos ('BBCA') -> ticker itu sendiri (jalur analyze cepat)
    - source 'compare:...' -> ticker pertama (jalur perbandingan)
    - source 'research:...' -> parse ulang query asli dari content (topic bukan ticker)
    - source None -> fallback parse content (pemanggil lama)
    """
    if source:
        if source.startswith("compare:"):
            first = source.split(":", 1)[1].split(",")[0].strip()
            return normalize(first) if first else None
        if not source.startswith("research:") and _CONTEXT_TICKER_SOURCE.match(source):
            return source
    m = re.search(r"'([^']*?)'", content)
    if not m:
        return None
    _, params = parse(m.group(1))
    if params.get("ticker"):
        return params["ticker"]
    tickers = params.get("tickers", "")
    if tickers:
        return tickers.replace(",", " ").split()[0]
    return None
