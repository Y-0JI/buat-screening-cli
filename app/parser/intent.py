import re

INTENT_ANALYZE = "analyze"
INTENT_SCREEN = "screen"
INTENT_COMPARE = "compare"
INTENT_GAINERS = "gainers"
INTENT_LOSERS = "losers"
INTENT_STOCKS = "stocks"
INTENT_HELP = "help"
INTENT_UNKNOWN = "unknown"


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
        t1 = compare_match.group(1).upper()
        t2 = compare_match.group(2).upper() if compare_match.group(2) else ""
        if len(t2) < 2:
            tickers = t1
        else:
            tickers = f"{t1},{t2}"
        return INTENT_COMPARE, {"tickers": tickers}

    if re.search(r"\b(?:info|help|bantuan|tolong|halo|hai|menu|perintah|command)\b", text_lower):
        return INTENT_HELP, {}

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
            ticker = m.group(1).upper()
            if len(ticker) <= 5 and ticker.isalpha():
                return INTENT_ANALYZE, {"ticker": ticker}

    return INTENT_UNKNOWN, {"text": text}
