import re

INTENT_ANALYZE = "analyze"
INTENT_SCREEN = "screen"
INTENT_COMPARE = "compare"
INTENT_HELP = "help"
INTENT_UNKNOWN = "unknown"


def parse_intent(text: str) -> tuple[str, dict]:
    text_lower = text.lower().strip()

    compare_match = re.search(r"bandingkan\s+(\w+)\s*(?:dan|,|vs|dengan)?\s*(\w*)", text_lower)
    if compare_match:
        t1 = compare_match.group(1).upper()
        t2 = compare_match.group(2).upper() if compare_match.group(2) else ""
        tickers = t1 if not t2 else f"{t1},{t2}"
        return INTENT_COMPARE, {"tickers": tickers}

    analyze_patterns = [
        r"analisa\s+(\w+)",
        r"analisis\s+(\w+)",
        r"apakah\s+(\w+)\s+layak",
        r"bagaimana\s+(?:dengan\s+)?(\w+)",
        r"cek\s+(\w+)",
        r"trend\s+(\w+)",
        r"score\s+(\w+)",
    ]
    for pat in analyze_patterns:
        m = re.search(pat, text_lower)
        if m:
            return INTENT_ANALYZE, {"ticker": m.group(1).upper()}

    if re.search(r"breakout|golden.cross|screening", text_lower):
        return INTENT_SCREEN, {"type": "all"}

    sector_match = re.search(r"(?:sektor|sector)\s+(\w+)", text_lower)
    if sector_match:
        return INTENT_SCREEN, {"type": "sector", "sector": sector_match.group(1)}

    if re.search(r"top\s+(?:gainers|naik)", text_lower):
        return INTENT_SCREEN, {"type": "top_gainers"}

    if re.search(r"top\s+(?:losers|turun)", text_lower):
        return INTENT_SCREEN, {"type": "top_losers"}

    if re.search(r"\b(?:info|help|bantuan|tolong|halo|hai)\b", text_lower):
        return INTENT_HELP, {}

    return INTENT_UNKNOWN, {"text": text}
