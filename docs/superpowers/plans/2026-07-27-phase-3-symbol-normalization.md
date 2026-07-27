# Phase 3 — Symbol Normalization Implementation Plan

> Instruksi untuk agent murah. Bahasa Indonesia high-level.

**Goal:** Satu fungsi canonical `normalize()` untuk semua symbol. Replace scattered `.upper()`/`.strip()` di boundary. Fix `.JK` duplication di validate_universe.

**Files:**
| Action | File |
|---|---|
| MODIFY | `app/validation.py` |
| MODIFY | `app/cli/main.py` |
| MODIFY | `app/parser/intent.py` |
| MODIFY | `app/agent/core.py` |
| MODIFY | `app/tools/__init__.py` |
| MODIFY | `app/tools/cache.py` |
| MODIFY | `app/services/stock_list.py` |
| MODIFY | `app/services/validate_universe.py` |
| MODIFY | `tests/test_validation.py` |

---

### Task 1: `app/validation.py` — tambah `normalize()`

```python
def normalize(ticker: str) -> str:
    return ticker.strip().upper()
```

Update `is_valid()` dan `validate()` panggil `normalize()` di dalamnya, bukan inline strip+upper.

---

### Task 2: Boundary files — replace scattered `.upper()`/`.strip()` with `normalize()`

**`app/cli/main.py`:** ganti `ticker.upper()` display calls jadi `normalize(ticker)`. Compare command: `t.strip().upper()` jadi `normalize(t)`.

**`app/parser/intent.py`:** ganti `w.upper()`, `m.group(1).upper()`, dll jadi `normalize()`.

**`app/agent/core.py`:** ganti `ticker.upper()`, `args[0].upper()`, dll jadi `normalize()`.

**`app/tools/__init__.py`:** di `FallbackProvider.fetch()` dan `get_price()`, panggil `normalize(ticker)` sebelum validasi + loop. Jadi safety net: semua yang masuk provider sudah normalized.

**`app/tools/cache.py`:** ganti `ticker.upper()` di `_path()` jadi `normalize(ticker)`.

**`app/services/stock_list.py`:** ganti `ticker.upper()` di `resolve_name()`/`resolve_sector()` jadi `normalize(ticker)`.

---

### Task 3: Fix `.JK` duplication di `validate_universe.py`

Di `app/services/validate_universe.py:22`, ganti `yf.download(ticker + ".JK")` dengan panggil `YahooFinanceProvider.fetch(ticker)`. Ini:
- Hapus duplikasi `.JK` logic
- Provider jadi satu-satunya tempat yang tahu suffix exchange
- validate_universe ikut kebagian retry + error handling dari YahooFinanceProvider

Butuh import `YahooFinanceProvider` di validate_universe.py. Method `fetch(` return `StockData | None` — dicek `if data is not None` untuk nentuin valid/tidak.

---

### Task 4: Tests

`tests/test_validation.py` — tambah:
- `test_normalize_strips_whitespace`: `"  BBCA  "` → `"BBCA"`
- `test_normalize_uppercases`: `"bbca"` → `"BBCA"`
- `test_normalize_idempotent`: `normalize(normalize(x)) == normalize(x)`

Jalanin full suite — pastikan 90+ tests lulus.

---

### Task 5: Verify

```bash
pytest tests/ -v
```
Expected: All pass. No behavior change — normalize() cuma formalisasi yang sudah terjadi scattered.
