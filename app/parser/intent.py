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
    type: Literal["single_stock", "sector_theme", "comparative", "screening_only", "analyze_only"]
    tickers: list[str]
    sector: str | None
    raw_query: str


def detect_research_intent(query: str) -> ResearchIntent:
    q = query.lower().strip()
    words = q.split()

    ticker_match = re.search(r'\b([A-Z]{3,5})\b', query.upper())
    if ticker_match and len(words) <= 3:
        return ResearchIntent("single_stock", [ticker_match.group(1)], None, query)
    if any(w in q for w in ["analisa", "analisis", "analyze"]):
        for w in words:
            if w.isalpha() and 3 <= len(w) <= 5:
                return ResearchIntent("single_stock", [normalize(w)], None, query)

    if any(w in q for w in ["bandingkan", "bandingin", "compare", "vs", "versus"]):
        tickers = [normalize(w) for w in words if w.isalpha() and 3 <= len(w) <= 5]
        if len(tickers) >= 2:
            return ResearchIntent("comparative", tickers[:2], None, query)

    sector_keywords = ["sektor", "sector", "screening", "cari", "temukan", "saham", "bagus"]
    if any(w in q for w in sector_keywords):
        for i, w in enumerate(words):
            if w in ["sektor", "sector"] and i + 1 < len(words):
                return ResearchIntent("sector_theme", [], words[i + 1].title(), query)
        return ResearchIntent("sector_theme", [], None, query)

    return ResearchIntent("sector_theme", [], None, query)


def parse(text: str) -> tuple[str, dict]:
    text_lower = text.lower().strip()

    if re.search(r"\b(?:gainers?|top\s+naik|top\s+gainer|saham\s+naik|paling\s+naik)\b", text_lower):
        return INTENT_GAINERS, {}

    if re.search(r"\b(?:losers?|top\s+turun|top\s+loser|saham\s+turun|paling\s+turun)\b", text_lower):
        return INTENT_LOSERS, {}

    compare_match = re.search(
        r"(?:bandingkan|compare|perbandingan|vs\.?|versus)\s+(\w{2,5})\s*(?:dan|,|&|vs\.?|dengan|sama)?\s*(\w{0,5})",
        text_lower,
    )
    if compare_match:
        t1 = normalize(compare_match.group(1))
        t2 = normalize(compare_match.group(2)) if compare_match.group(2) else ""
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

    sector_match = re.search(r"(?:sektor|sector)\s+(\w+)", text_lower)
    if sector_match:
        return INTENT_SCREEN, {"type": "sector", "sector": sector_match.group(1)}

    if re.search(r"\b(?:stocks?|daftar|list|emiten|saham\s+aja)\b", text_lower):
        return INTENT_STOCKS, {}

    analyze_patterns = [
        r"(?:analisa|analisis|analisislah|cek|lihat|periksa|bagaimana|kondisi|review)\s+(\w+)",
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
