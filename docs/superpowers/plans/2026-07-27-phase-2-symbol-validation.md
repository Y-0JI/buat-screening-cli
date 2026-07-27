# Phase 2 — Symbol Validation Implementation Plan

> Instruksi untuk agent murah. Bahasa Indonesia high-level.

**Goal:** Cegah ticker invalid masuk ke provider. Validasi di 2 layer: FallbackProvider (gate) + CLI (pre-check UX).

**Files:**
| Action | File |
|---|---|
| CREATE | `app/validation.py` |
| MODIFY | `app/tools/__init__.py` |
| MODIFY | `app/cli/main.py` |
| MODIFY | `app/router/engine.py` |
| CREATE | `tests/test_validation.py` |
| MODIFY | `tests/test_cli.py` |
| MODIFY | `tests/test_router.py` |

---

### Task 1: `app/validation.py` — SymbolValidator

File baru. Satu-satunya source of truth untuk aturan format symbol.

```python
import re

_RULE = re.compile(r"^[A-Z0-9.]{1,10}$")

def is_valid(symbol: str) -> bool:
    return bool(_RULE.match(symbol))

def validate(symbol: str) -> str | None:
    if not symbol or not symbol.strip():
        return "Symbol tidak boleh kosong"
    if not _RULE.match(symbol.strip().upper()):
        return f"Format symbol tidak valid: '{symbol}'. Gunakan 1-10 karakter alfanumerik atau titik."
    return None
```

Aturan: `^[A-Z0-9.]{1,10}$` — baseline untuk semua provider. Kalau nanti ada provider-specific rules, tambah parameter `provider_name` di `validate()`.

---

### Task 2: `app/tools/__init__.py` — Gate di FallbackProvider

Di `FallbackProvider.fetch()` dan `get_price()`, validasi symbol SEBELUM loop provider.

```python
from app.validation import is_valid

def fetch(self, ticker, period="6mo", need_profile=True):
    if not is_valid(ticker):
        logger.warning(f"Invalid symbol: {ticker}")
        return None

def get_price(self, ticker):
    if not is_valid(ticker):
        return None
```

Ini satu-satunya authoritative gate. Semua jalur (CLI, AI, bulk, future) lewat sini.

---

### Task 3: `app/cli/main.py` — Pre-check CLI

Di command handler `analyze`, `trend`, `score`, `compare`, validasi input user PAKAI `validation.validate()` YANG SAMA.

```python
from app.validation import validate

@app.command()
def analyze(ticker: str):
    err = validate(ticker)
    if err:
        _p.error(err)
        raise typer.Exit(1)
    ...
```

Sama untuk trend, score, compare. Ini cuma UX — FallbackProvider tetap gate utama.

---

### Task 4: `app/router/engine.py` — Fix `_fetch_and_screen`

Di `_fetch_and_screen()`:

```python
def _fetch_and_screen(t: str):
    ...
    if not data:
        return None, "not_found"  # WAS: "error"
```

Biar list `invalid` di `bulk_screen()` benar-benar terisi. Ini bug existing.

---

### Task 5: Tests

**`tests/test_validation.py` — 5 test:**
1. `test_valid_symbols`: BBCA, A, BRK.A, A1, 12345 → valid
2. `test_invalid_symbols`: "", "TOOLONGG", "ab cd", "a b c" → invalid
3. `test_validate_returns_message`: invalid → return string error
4. `test_validate_returns_none`: valid → return None

**`tests/test_cli.py` — update**: tambah test:
- `test_analyze_invalid_ticker`: input "123" → exit_code != 0
- `test_trend_invalid_ticker`: input "" → exit_code != 0
- `test_score_invalid_ticker`: input "TOOLONG" → exit_code != 0

**`tests/test_router.py` — update**: 
- `test_fallback_invalid_symbol`: FallbackProvider.fetch("") → None
- `test_bulk_screen_not_found`: pastikan invalid list terisi

---

### Task 6: Verify

```bash
pytest tests/test_validation.py tests/test_cli.py tests/test_router.py -v
```

Expected: All pass.

```bash
pytest tests/ -v
```

Expected: All pass, no existing test broken.
