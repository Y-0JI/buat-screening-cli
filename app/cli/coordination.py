"""Koordinasi Phase 2 — routing workflow, orchestration multi-klausa.

Semua keputusan workflow ada di lapisan ini; parser tetap pure (hanya data).
Helper di sini murni (input -> output), tanpa I/O storage/network. Follow-up
percakapan kini ditangani satu jalur di app.cli.conversation (Phase 3).
"""

import re
from dataclasses import dataclass

from app.parser.ambiguity import split_clauses
from app.parser.intent import ParseResult

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