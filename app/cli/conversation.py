"""Conversation State Phase 3 — satu sumber konteks percakapan saat ini.

Pemanggil (natural/chat) hanya pakai record/recent/resolve_followup; detail
penyimpanan internal: satu entri rolling IMPORTANT_CONTEXT (source='conversation'),
di-overwrite tiap aksi sukses. Tidak menyimpan hasil analisis / riwayat —
cukup ticker aktif + workflow + query inti untuk follow-up berikutnya.

Resolver rule-based untuk pola jelas; di luar pola -> None (alur normal yang
memutuskan). Bukan parser kedua, tanpa interpretasi bebas.

Reset (clear) sengaja tidak disediakan: state di-replace tiap aksi sukses,
absen entri = kosong, dan akhir sesi chat mempertahankan state untuk
kontinuitas. Tambahkan clear() via store.forget bila alur reset eksplisit
dibutuhkan (keputusan desain, bukan fitur terlupakan).
"""

import re
from dataclasses import dataclass

from app.memory import get_store
from app.memory.models import MemoryType
from app.cli.coordination import _canonical_ticker

_SOURCE = "conversation"


@dataclass
class ConversationState:
    workflow: str
    tickers: tuple[str, ...]
    query: str


def record(workflow: str, tickers, query: str) -> None:
    state = ConversationState(workflow=workflow, tickers=tuple(tickers), query=query)
    get_store().add_or_update(MemoryType.IMPORTANT_CONTEXT, _content(state), source=_SOURCE)


def recent() -> ConversationState | None:
    for e in reversed(get_store().get_all()):
        if e.type == MemoryType.IMPORTANT_CONTEXT and e.source == _SOURCE:
            return _parse(e.content)
    return None


def _content(state: ConversationState) -> str:
    return f"{state.workflow}|{','.join(state.tickers)}|{state.query}"


def _parse(content: str) -> ConversationState | None:
    parts = content.split("|", 2)
    if len(parts) != 3:
        return None
    workflow, tickers, query = parts
    return ConversationState(
        workflow=workflow,
        tickers=tuple(t for t in tickers.split(",") if t),
        query=query,
    )


_RX_COMPARE_ONE = re.compile(
    r"^(?:bandingkan\s+dengan|bandingkan|vs\.?|versus)\s+(\w{2,5})\s*\??$", re.IGNORECASE
)
_RX_ANALYZE_OTHER = re.compile(
    r"^(?:"
    r"kalau\s+(\w{2,5})(?:\s+gimana)?"
    r"|gimana\s+dengan\s+(\w{2,5})"
    r"|bagaimana\s+dengan\s+(\w{2,5})"
    r"|terus\s+(\w{2,5})(?:\s+gimana)?"
    r")\??$",
    re.IGNORECASE,
)
_RX_PRONOUN = re.compile(r"\b(?:saham\s+itu|saham\s+tersebut|yang\s+tadi|dia|itu)\b", re.IGNORECASE)
_ANCHOR_VERB = re.compile(r"\b(?:bandingkan|vs\.?|versus|kalau|gimana|bagaimana|terus)\b", re.IGNORECASE)


def resolve_followup(query: str, state: ConversationState | None, universe=None) -> str | None:
    """Lengkapi query pendek dengan konteks percakapan saat ini. Pola jelas
    saja; di luar pola -> None (query jalan normal). Tidak menyentuh storage —
    pemanggil yang ambil state via recent()."""
    if not state or not state.tickers:
        return None
    anchor = state.tickers[0]

    stripped = query.strip()
    q = stripped
    if _RX_PRONOUN.search(stripped):
        short = len(stripped.rstrip("? ").split()) <= 2
        if short or _ANCHOR_VERB.search(stripped):
            q = re.sub(_RX_PRONOUN, anchor, stripped)

    m = _RX_COMPARE_ONE.match(q)
    if m:
        return f"bandingkan {anchor} dan {_canonical_ticker(m.group(1), universe)}"

    m = _RX_ANALYZE_OTHER.match(q)
    if m:
        raw = next(g for g in m.groups() if g)
        return f"analisa {_canonical_ticker(raw, universe)}"

    if q != stripped:
        return q
    return None
