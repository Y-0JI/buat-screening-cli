"""Ambiguity detection for parsed queries. Pure functions — no I/O, no workflow.

`universe` di-inject pemanggil (CLI/TUI/API/Web) sebagai source of truth
validitas ticker; parser tetap pure dan reusable di mana pun. `universe=None`
berarti cek berbasis universe dilewati (multi-intent tetap terdeteksi).
"""

import re
from dataclasses import dataclass, field

from app.validation import normalize


@dataclass
class AmbiguityResult:
    ambiguous: bool = False
    reason: str = ""
    candidates: list[str] = field(default_factory=list)
    invalid: list[str] = field(default_factory=list)


def params_tickers(params: dict) -> list[str]:
    out = []
    ticker = params.get("ticker")
    if ticker:
        out.append(ticker)
    for t in params.get("tickers", "").replace(",", " ").split():
        if t:
            out.append(t)
    return out


def _known_tickers(universe) -> set[str] | None:
    if universe is None:
        return None
    return {normalize(s["ticker"]) for s in universe}


def detect_invalid_ticker(intent: str, params: dict, universe) -> list[str]:
    """Ticker di params yang tidak dikenal. [] kalau unknown atau tanpa universe.

    Matching toleran: ticker params valid kalau exact match ATAU ada ticker universe
    yang berakhiran params (contoh: "bca" -> BBCA, "bri" -> BBRI) — bahasa
    sehari-hari Indonesia biasa menyebut saham tanpa huruf depan.
    """
    if universe is None:
        return []
    known = sorted(_known_tickers(universe))
    invalid = []
    for t in params_tickers(params):
        nt = normalize(t)
        matched = any(tk == nt or tk.endswith(nt) for tk in known)
        if not matched:
            invalid.append(t)
    return invalid


# TODO Phase 2: multi-intent akan jadi workflow orchestration
# (jalankan beberapa workflow terkoordinasi), bukan ambiguity.
# Saat itu, fungsi ini dipindah/diubah, bukan dihapus sembarangan.
_MULTI_INTENT_PATTERNS = [
    ("analyze", r"\b(?:analisa|analisis|cek|lihat|periksa|review|bagaimana|kondisi)\b"),
    ("compare", r"\b(?:bandingkan|compare|perbandingan|vs\.?|versus)\b"),
    ("screen", r"\b(?:breakout|golden\s*cross|screening|rekomendasi|cari\s+saham)\b"),
    ("research", r"\b(?:riset|research|penelitian|studi)\b"),
    ("gainers", r"\b(?:gainers?|top\s+naik|top\s+gainer|saham\s+naik|paling\s+naik)\b"),
    ("losers", r"\b(?:losers?|top\s+turun|saham\s+turun|paling\s+turun)\b"),
]

# Pemisah KLAUSA yang jelas — dua kata kunci dalam SATU kalimat tanpa pemisah
# bukan berarti dua maksud ("analisa kondisi breakout BCA" = satu maksud).
_CLAUSE_SEPARATORS = r"(?:lalu|terus|kemudian|selanjutnya|selain\s+itu|setelah\s+itu|dan\s+juga|serta|tapi|tetapi|namun)"


def detect_multi_intent(query: str, universe) -> bool:
    """Multi-intent = >=2 klausa terpisah pemisah jelas, masing-masing punya
    kata kunci intent kuat, dengan >=2 kategori BERBEDA. Satu kalimat dengan
    dua kata kunci (misal "analisa kondisi breakout BCA") = SATU maksud.
    """
    clauses = [c for c in re.split(_CLAUSE_SEPARATORS, query.lower()) if c.strip()]
    if len(clauses) < 2:
        return False
    all_intents: set[str] = set()
    for clause in clauses:
        matched = {label for label, pat in _MULTI_INTENT_PATTERNS if re.search(pat, clause)}
        all_intents |= matched
    return len(all_intents) >= 2


def _name_tokens(name: str) -> set[str]:
    """Token kata utuh (>=3 huruf, non-alpha dibuang) dari nama perusahaan."""
    tokens = set()
    for raw in name.lower().split():
        token = re.sub(r"[^a-z]", "", raw)
        if len(token) >= 3:
            tokens.add(token)
    return tokens


def detect_company_candidates(word: str, universe) -> list[str]:
    """Kandidat ticker: `word` (>=3 huruf) harus TOKEN UTUH di nama perusahaan,
    bukan substring — "sari" tidak cocok ke "Indosari". [] kalau tak cocok."""
    if not word or universe is None or len(word) < 3:
        return []
    w = word.lower()
    out = []
    for s in universe:
        if w in _name_tokens(s["name"]):
            out.append(s["ticker"])
    return out[:5]


def detect_ambiguity(query: str, intent: str, params: dict, universe) -> AmbiguityResult:
    """Orchestrator: gabung hasil helper. Ambigu kalau multi-intent, ticker invalid,
    atau kata yang cocok nama perusahaan (bukan ticker)."""
    if detect_multi_intent(query, universe):
        return AmbiguityResult(True, "multi_intent", [])
    invalid = detect_invalid_ticker(intent, params, universe)
    if invalid:
        # Regex parser bisa memotong kata panjang ("telekomunikasi" -> "tele").
        # Expand ke kata UTUH di query supaya kandidat & substitusi benar.
        words = re.findall(r"[a-z]{3,}", query.lower())
        full_words = []
        for t in invalid:
            full = next((w for w in words if t.lower() in w), t.lower())
            if full not in full_words:
                full_words.append(full)
        candidates = []
        for w in full_words:
            candidates.extend(detect_company_candidates(w, universe))
        return AmbiguityResult(True, "invalid_ticker", candidates[:5], full_words)
    if intent == "unknown":
        for word in re.findall(r"[a-z]{2,}", query.lower()):
            candidates = detect_company_candidates(word, universe)
            if candidates:
                return AmbiguityResult(True, "company_candidate", candidates, [word])
    return AmbiguityResult()
