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


def detect_multi_intent(query: str, universe) -> bool:
    text = query.lower()
    matched = {label for label, pat in _MULTI_INTENT_PATTERNS if re.search(pat, text)}
    return len(matched) >= 2


def detect_company_candidates(word: str, universe) -> list[str]:
    """Kandidat ticker dari nama perusahaan yang mengandung `word`. [] kalau tak cocok."""
    if not word or universe is None:
        return []
    return [s["ticker"] for s in universe if word.lower() in s["name"].lower()][:5]


def detect_ambiguity(query: str, intent: str, params: dict, universe) -> AmbiguityResult:
    """Orchestrator: gabung hasil helper. Ambigu kalau multi-intent, ticker invalid,
    atau kata yang cocok nama perusahaan (bukan ticker)."""
    if detect_multi_intent(query, universe):
        return AmbiguityResult(True, "multi_intent", [])
    invalid = detect_invalid_ticker(intent, params, universe)
    if invalid:
        candidates = []
        for t in invalid:
            candidates.extend(detect_company_candidates(t, universe))
        return AmbiguityResult(True, "invalid_ticker", candidates[:5])
    if intent == "unknown":
        for word in re.findall(r"[a-z]{2,}", query.lower()):
            candidates = detect_company_candidates(word, universe)
            if candidates:
                return AmbiguityResult(True, "company_candidate", candidates)
    return AmbiguityResult()
