import re

_RULE = re.compile(r"^[A-Z0-9.]{1,10}$")


def normalize(ticker: str) -> str:
    return ticker.strip().upper()


def is_valid(symbol: str) -> bool:
    return bool(_RULE.match(normalize(symbol)) if symbol else False)


def validate(symbol: str) -> str | None:
    if not symbol or not symbol.strip():
        return "Symbol tidak boleh kosong"
    if not _RULE.match(normalize(symbol)):
        return f"Format symbol tidak valid: '{symbol}'. Gunakan 1-10 karakter alfanumerik atau titik."
    return None
