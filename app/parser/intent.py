import re
from dataclasses import dataclass, field
from typing import Literal
from app.validation import normalize
from app.parser.ambiguity import AmbiguityResult, detect_ambiguity, params_tickers


INTENT_ANALYZE = "analyze"
INTENT_SCREEN = "screen"
INTENT_COMPARE = "compare"
INTENT_GAINERS = "gainers"
INTENT_LOSERS = "losers"
INTENT_STOCKS = "stocks"
INTENT_HELP = "help"
INTENT_RESEARCH = "research"
INTENT_UNKNOWN = "unknown"

# Verb analisa eksplisit + satu kata (2-5 huruf) di ujung kalimat — pola utama
# analyze. Dipakai pre-screen (analyze menang atas screen saat verb jelas)
# dan di loop analyze_patterns.
_ANALYZE_ANCHOR_PATTERN = r"(?:analisa|analisis|analisislah|cek|lihat|periksa|bagaimana|kondisi|review|berita|fundamental|teknikal|lengkap)\s+.*?\b(\w{2,5})\W*$"


@dataclass
class ParseResult:
    """Hasil parse penuh: intent, params, confidence, ambiguity. Data murni —
    parser tidak pernah mengeksekusi apa pun berdasarkan ini (routing = caller)."""

    intent: str
    params: dict
    confidence: Literal["high", "medium", "low"]
    ambiguity: AmbiguityResult = field(default_factory=AmbiguityResult)


def parse(text: str) -> tuple[str, dict]:
    """Backward-compat wrapper: parse_full tanpa metadata."""
    result = parse_full(text)
    return result.intent, result.params


def parse_full(text: str, universe=None) -> ParseResult:
    """Pipeline parser:

        Natural language
             ↓
        Intent detection
             ↓
        Entity extraction
             ↓
        Ambiguity detection
             ↓
        Confidence assignment
             ↓
        ParseResult

    Pure: tidak membaca input user, tidak memanggil CLI/fetch, tidak menjalankan
    workflow — bisa dipakai ulang oleh CLI, TUI, API, maupun Web. `universe`
    (opsional) di-inject pemanggil sebagai source of truth validitas ticker.
    Routing keputusan (analyze vs research, dst) adalah scope Phase 2 — tidak
    ada di sini.
    """
    intent, params = _parse(text)
    intent, params = _reinterpret_saham_sector(text, intent, params, universe)
    ambiguity = detect_ambiguity(text, intent, params, universe)
    confidence = _assign_confidence(text, intent, params, universe, ambiguity)
    return ParseResult(intent, params, confidence, ambiguity)


def _reinterpret_saham_sector(text: str, intent: str, params: dict, universe) -> tuple[str, dict]:
    """Kalimat 'saham X' di mana X bukan ticker yang dikenal -> interpretasi sektor.

    Contoh: 'saham bank' -> SCREEN sector bank. 'saham BBCA' (ticker valid) tetap
    ANALYZE. Interpretasi intent, bukan routing workflow — pure, universe di-inject.
    """
    if universe is None or intent != INTENT_ANALYZE:
        return intent, params
    ticker = params.get("ticker")
    if not ticker:
        return intent, params
    known = {normalize(s["ticker"]) for s in universe}
    if normalize(ticker) in known:
        return intent, params
    m = re.match(r"^saham\s+(\w+)$", text.strip().lower())
    if m:
        return INTENT_SCREEN, {"type": "sector", "sector": m.group(1)}
    return intent, params


def _assign_confidence(text: str, intent: str, params: dict, universe, ambiguity: AmbiguityResult) -> str:
    if ambiguity.ambiguous or intent == INTENT_UNKNOWN:
        return "low"
    if re.match(r"^\w{2,5}$", text.strip().lower()):
        return "low"
    if universe is None:
        return "medium"
    known = {normalize(s["ticker"]) for s in universe}
    tickers = params_tickers(params)
    if tickers and all(normalize(t) in known for t in tickers):
        return "high"
    return "medium"


@dataclass
class ResearchIntent:
    type: Literal["single_stock", "sector_theme", "comparative", "screening_only", "analyze_only", "unsupported"]
    tickers: list[str]
    sector: str | None
    raw_query: str


def _extract_sector(text: str) -> str | None:
    m = re.search(r"(?:sektor|sector)\s+(\w+)", text.lower())
    return m.group(1) if m else None


def detect_research_intent(query: str) -> ResearchIntent:
    intent, params = parse(query)
    if intent == INTENT_ANALYZE:
        ticker = params.get("ticker", "")
        return ResearchIntent("single_stock", [ticker] if ticker else [], None, query)
    if intent == INTENT_COMPARE:
        tickers = [normalize(t) for t in params.get("tickers", "").replace(",", " ").split() if t]
        return ResearchIntent("comparative", tickers, None, query)
    if intent == INTENT_SCREEN:
        return ResearchIntent("sector_theme", [], params.get("sector") or _extract_sector(query), query)
    if intent == INTENT_RESEARCH:
        return ResearchIntent("sector_theme", [], _extract_sector(query), query)
    return ResearchIntent("unsupported", [], None, query)


def _parse(text: str) -> tuple[str, dict]:
    text_lower = text.lower().strip()

    if re.search(r"\b(?:gainers?|top\s+naik|top\s+gainer|saham\s+naik|paling\s+naik|saham\s+apa\s+yang\s+naik)\b", text_lower):
        return INTENT_GAINERS, {}

    if re.search(r"\b(?:losers?|top\s+turun|top\s+loser|saham\s+turun|paling\s+turun)\b", text_lower):
        return INTENT_LOSERS, {}

    better_match = re.search(
        r"(?:mana\s+yang\s+lebih\s+baik|lebih\s+baik)\s+(\w{2,5})\s+(?:atau|dan)\s+(\w{2,5})",
        text_lower,
    )
    if better_match:
        t1, t2 = normalize(better_match.group(1)), normalize(better_match.group(2))
        return INTENT_COMPARE, {"tickers": f"{t1},{t2}"}

    compare_match = re.search(
        r"(\w{2,5})\s+(?:vs\.?|versus)\s+(\w{2,5})"
        r"|(?:bandingkan|compare|perbandingan|vs\.?|versus)\s+(\w{2,5})\s*(?:dan|,|&|vs\.?|dengan|sama)?\s*(\w{0,5})",
        text_lower,
    )
    if compare_match:
        if compare_match.group(1):
            t1, t2 = normalize(compare_match.group(1)), normalize(compare_match.group(2))
        else:
            t1, t2 = normalize(compare_match.group(3)), normalize(compare_match.group(4))
        if len(t2) < 2:
            tickers = t1
        else:
            tickers = f"{t1},{t2}"
        return INTENT_COMPARE, {"tickers": tickers}

    if re.search(r"\b(?:info|help|bantuan|tolong|halo|hai|menu|perintah|command)\b", text_lower):
        return INTENT_HELP, {}

    if re.search(r"\b(?:riset|research|penelitian|studi)\b", text_lower):
        return INTENT_RESEARCH, {"text": text}

    anchor = re.search(_ANALYZE_ANCHOR_PATTERN, text_lower)
    if anchor:
        ticker = normalize(anchor.group(1))
        if len(ticker) <= 5 and ticker.isalpha():
            return INTENT_ANALYZE, {"ticker": ticker}

    if re.search(r"breakout|golden\s*cross|screening|saham\s+apa|rekomendasi|cari\s+saham", text_lower):
        return INTENT_SCREEN, {"type": "all"}

    sector_match = _extract_sector(text_lower)
    if sector_match:
        return INTENT_SCREEN, {"type": "sector", "sector": sector_match}

    if re.search(r"\b(?:stocks?|daftar|list|emiten|saham\s+aja)\b", text_lower):
        return INTENT_STOCKS, {}

    analyze_patterns = [
        _ANALYZE_ANCHOR_PATTERN,
        r"apakah\s+(\w+)\s+layak",
        r"bagaimana\s+(?:dengan\s+)?(\w+)",
        r"^(?:saham\s+)?(\w{2,5})$",
        r"trend\s+(\w+)",
        r"score\s+(\w+)",
        r"kenapa\s+(\w+)\s+turun",
        r"(\w+)\s+bagus(?:\s+(?:nggak|ngga|gak|enggak))?\s*$",
        r"kelayakan\s+(\w+)",
        r"(?:mau|ingin)\s+beli\s+(\w+)",
        r"nasib\s+(\w+)",
    ]
    for pat in analyze_patterns:
        m = re.search(pat, text_lower)
        if m:
            ticker = normalize(m.group(1))
            if len(ticker) <= 5 and ticker.isalpha():
                return INTENT_ANALYZE, {"ticker": ticker}

    saham_sector = re.match(r"saham\s+(\w+)$", text_lower)
    if saham_sector:
        return INTENT_SCREEN, {"type": "sector", "sector": saham_sector.group(1)}

    return INTENT_UNKNOWN, {"text": text}
