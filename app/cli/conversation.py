"""Conversation State Phase 3 — satu sumber konteks percakapan saat ini.

Pemanggil (natural/chat) hanya pakai record/recent/resolve_followup; detail
penyimpanan internal: satu entri rolling IMPORTANT_CONTEXT (source='conversation'),
di-overwrite tiap aksi sukses. Tidak menyimpan hasil analisis / riwayat —
cukup ticker aktif + workflow + query inti untuk follow-up berikutnya.

Resolver rule-based untuk pola jelas; di luar pola -> None (alur normal yang
memutuskan). Bukan parser kedua, tanpa interpretasi bebas. Satu-satunya
mekanisme follow-up (menggantikan coordination.resolve_followup lama).

Reset (clear) sengaja tidak disediakan: state di-replace tiap aksi sukses,
absen entri = kosong, dan akhir sesi chat mempertahankan state untuk
kontinuitas. Tambahkan clear() via store.forget bila alur reset eksplisit
dibutuhkan (keputusan desain, bukan fitur terlupakan).
"""

import re
from dataclasses import dataclass

from app.memory import get_store
from app.memory.models import MemoryType
from app.validation import normalize

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


def extract_tickers(query: str, universe=None) -> list[str]:
    """Ekstrak ticker berbasis universe (exact / suffix-match, toleran sama
    seperti parser). Dipakai workflow yang parameternya bukan ticker
    (research: 'riset bbca' -> BBCA); kata umum tanpa kecocokan universe
    diabaikan ('riset bank' -> [])."""
    if not universe:
        return []
    result: list[str] = []
    for tok in re.findall(r"\b\w{2,6}\b", query):
        t = tok.lower()
        for s in universe:
            tk = normalize(s["ticker"]).lower()
            if tk == t or tk.endswith(t):
                canonical = normalize(s["ticker"])
                if canonical not in result:
                    result.append(canonical)
                break
    return result


def _canonical_ticker(raw: str, universe) -> str:
    """Kanonikali ticker pendek via universe: exact match atau suffix-match
    ('bri' -> BBRI), pola toleran yang sama dengan ambiguity.py. Tanpa universe
    -> raw hasil normalize."""
    t = normalize(raw)
    if universe:
        for s in universe:
            tk = normalize(s["ticker"])
            if tk == t or tk.endswith(t):
                return tk
    return t


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
    if not state:
        return None
    anchor = state.tickers[0] if state.tickers else None

    stripped = query.strip()
    q = stripped
    if _RX_PRONOUN.search(stripped):
        short = len(stripped.rstrip("? ").split()) <= 2
        if anchor and (short or _ANCHOR_VERB.search(stripped)):
            q = re.sub(_RX_PRONOUN, anchor, stripped)

    if anchor:
        m = _RX_COMPARE_ONE.match(q)
        if m:
            return f"bandingkan {anchor} dan {_canonical_ticker(m.group(1), universe)}"

    m = _RX_ANALYZE_OTHER.match(q)
    if m:
        raw = next(g for g in m.groups() if g)
        return f"analisa {_canonical_ticker(raw, universe)}"

    if q != stripped:
        return _canonicalize_ticker_tokens(q, universe)
    return None


def _canonicalize_ticker_tokens(query: str, universe) -> str:
    """Kanonikali token ticker pendek di query (sama seperti jalur compare /
    analyze-other): 'bri' -> BBRI via universe. Kata yang bukan ticker tidak
    diubah (hasil kanonik == huruf besar aslinya)."""
    if not universe:
        return query

    def _repl(m):
        canon = _canonical_ticker(m.group(0), universe)
        return canon if canon != m.group(0).upper() else m.group(0)

    return re.sub(r"\b\w{2,5}\b", _repl, query)