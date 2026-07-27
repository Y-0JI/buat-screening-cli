# Phase 4 — Symbol Deduplication Implementation Plan

> Instruksi untuk agent murah. Bahasa Indonesia high-level.

**Goal:** Infrastruktur dedup untuk multi-provider symbol list. Tambah `list_symbols()`, `SymbolInfo` model, `merge_and_dedup()`. Tidak ada behavior change.

**Files:**
| Action | File |
|---|---|
| CREATE | `app/models/symbol.py` |
| MODIFY | `app/tools/yahoo_finance.py` |
| MODIFY | `app/tools/idx.py` |
| MODIFY | `app/tools/__init__.py` |
| MODIFY | `app/services/stock_list.py` |
| CREATE | `tests/test_dedup.py` |

---

### Task 1: `app/models/symbol.py` — SymbolInfo dataclass

File baru:

```python
from dataclasses import dataclass

@dataclass
class SymbolInfo:
    ticker: str
    name: str | None = None
    sector: str | None = None
```

Ini tipe return untuk `list_symbols()` dan input untuk `merge_and_dedup()`. Typed, bukan dict.

---

### Task 2: Provider `list_symbols()` — return empty

Tambah method ke kedua provider. Return `list[SymbolInfo]` kosong.

**`app/tools/yahoo_finance.py`:**
```python
from app.models.symbol import SymbolInfo

def list_symbols(self) -> list[SymbolInfo]:
    return []
```

**`app/tools/idx.py`:**
```python
from app.models.symbol import SymbolInfo

def list_symbols(self) -> list[SymbolInfo]:
    return []
```

Keduanya kosong. Implementasi real akan diisi di Phase 6 nanti.

---

### Task 3: `app/tools/__init__.py` — FallbackProvider.list_symbols()

```python
from app.models.symbol import SymbolInfo

class FallbackProvider:
    def list_symbols(self) -> list[SymbolInfo]:
        results = []
        for provider in self.providers:
            results.extend(provider.list_symbols())
        return results
```

Siap untuk multi-source. Saat ini return empty list.

---

### Task 4: `app/services/stock_list.py` — merge_and_dedup()

```python
from app.models.symbol import SymbolInfo

def merge_and_dedup(sources: list[list[SymbolInfo]]) -> list[SymbolInfo]:
    seen: dict[str, SymbolInfo] = {}
    for symbols in sources:
        for sym in symbols:
            t = normalize(sym.ticker) if sym.ticker else ""
            if not t:
                continue
            if t not in seen:
                seen[t] = sym
    return list(seen.values())
```

Pure infrastructure. Tidak dipanggil oleh `get_all()`.

---

### Task 5: Tests

`tests/test_dedup.py`:
1. `test_merge_no_duplicates`: gabung 2 list tanpa overlap → total length sum
2. `test_merge_with_duplicates`: gabung 2 list dengan 1 overlap → count = unique
3. `test_merge_empty`: list kosong → []
4. `test_list_symbols_empty`: YahooFinanceProvider.list_symbols() → []
5. `test_fallback_list_symbols_empty`: FallbackProvider.list_symbols() → []

---

### Task 6: Verify

```bash
pytest tests/test_dedup.py tests/test_yahoo_finance.py tests/test_idx_provider.py -v
```

Expected: All pass.

```bash
pytest tests/ -v
```

Expected: All existing tests masih lulus.
