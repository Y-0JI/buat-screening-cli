import re
from dataclasses import dataclass
from typing import Literal
from app.validation import normalize


INTENT_ANALYZE = "analyze"
INTENT_SCREEN = "screen"
INTENT_COMPARE = "compare"
INTENT_GAINERS = "gainers"
INTENT_LOSERS = "losers"
INTENT_STOCKS = "stocks"
INTENT_HELP = "help"
INTENT_RESEARCH = "research"
INTENT_UNKNOWN = "unknown"


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


def parse(text: str) -> tuple[str, dict]:
    text_lower = text.lower().strip()

    if re.search(r"\b(?:gainers?|top\s+naik|top\s+gainer|saham\s+naik|paling\s+naik)\b", text_lower):
        return INTENT_GAINERS, {}

    if re.search(r"\b(?:losers?|top\s+turun|top\s+loser|saham\s+turun|paling\s+turun)\b", text_lower):
        return INTENT_LOSERS, {}

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

    if re.search(r"breakout|golden\s*cross|screening|saham\s+apa|rekomendasi|cari\s+saham", text_lower):
        return INTENT_SCREEN, {"type": "all"}

    sector_match = _extract_sector(text_lower)
    if sector_match:
        return INTENT_SCREEN, {"type": "sector", "sector": sector_match}

    if re.search(r"\b(?:stocks?|daftar|list|emiten|saham\s+aja)\b", text_lower):
        return INTENT_STOCKS, {}

    analyze_patterns = [
        r"(?:analisa|analisis|analisislah|cek|lihat|periksa|bagaimana|kondisi|review|fundamental|teknikal|lengkap)\s+.*?\b(\w{2,5})\W*$",
        r"apakah\s+(\w+)\s+layak",
        r"bagaimana\s+(?:dengan\s+)?(\w+)",
        r"^(?:saham\s+)?(\w{2,5})$",
        r"trend\s+(\w+)",
        r"score\s+(\w+)",
    ]
    for pat in analyze_patterns:
        m = re.search(pat, text_lower)
        if m:
            ticker = normalize(m.group(1))
            if len(ticker) <= 5 and ticker.isalpha():
                return INTENT_ANALYZE, {"ticker": ticker}

    return INTENT_UNKNOWN, {"text": text}
