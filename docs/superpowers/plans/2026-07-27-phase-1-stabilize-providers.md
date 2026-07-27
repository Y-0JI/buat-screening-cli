# Phase 1 — Stabilize Data Providers Implementation Plan

> Instruksi untuk agent murah. Bahasa Indonesia high-level.

**Goal:** Auto-fallback antar provider, IDX retry, cache disk, konfigurasi via `.env`.

**Files:**
| Action | File |
|---|---|
| CREATE | `app/tools/cache.py` |
| MODIFY | `app/tools/__init__.py` |
| MODIFY | `app/tools/idx.py` |
| MODIFY | `app/config/settings.py` |
| CREATE | `tests/test_cache.py` |
| CREATE | `tests/test_fallback.py` |

**Tidak disentuh:** `stock_list.py`, `validate_universe.py`, `yahoo_finance.py`, `engine.py`, CLI apapun.

---

### Task 1: `app/config/settings.py` — Tambah config

Tambah 2 field di class `Settings`:
- `provider_fallback_order: str = "yahoo,idx"`
- `provider_cache_ttl_hours: int = 24`

Bisa dibaca dari `.env` dengan prefix `PROVIDER_`. Pydantic-settings handle otomatis.

---

### Task 2: `app/tools/cache.py` — Disk cache

File baru. Isi:
- `class ProviderCache`
- `__init__(cache_dir, ttl_hours)` — `cache_dir` default `app/data/provider_cache/`
- `_key(ticker, period, need_profile)` — return hash string
- `_path(key)` — return `{cache_dir}/{key}.json`
- `save(ticker, period, need_profile, data: StockData)` — serialize via `model_dump_json()`, tulis file
- `load(ticker, period, need_profile) -> StockData | None` — baca file, cek TTL via `os.path.getmtime()`. Kalau masih fresh → deserialize via `StockData.model_validate_json()`. Kalau expired → return None.
- `load_stale(ticker, period, need_profile) -> StockData | None` — sama tapi ignore TTL (buat fallback saat semua provider mati)
- Logging: cache hit, miss, save, stale warning

Ponytail: simpen per hash file. Hash cukup `md5(f"{ticker}:{period}:{need_profile}".encode()).hexdigest()[:16]`. Stdlib aja.

---

### Task 3: `app/tools/idx.py` — Retry IDX

Bungkus fetch body dengan `for attempt in range(3)`:
- attempt 0: normal fetch
- attempt 1-2: `time.sleep(attempt)`, retry
- `except Exception`: log warning, retry
- 3 gagal → `logger.warning(...)` → return `None`

Jangan tambah classifikasi error atau rate limit — cukup retry sederhana.

---

### Task 4: `app/tools/__init__.py` — FallbackProvider

Tambah di file yang sama:

**`FallbackProvider` class:**
- `__init__(self, providers: list, cache: ProviderCache)` — simpan daftar provider urut prioritas + cache instance
- `fetch(self, ticker, period="6mo", need_profile=True) -> StockData | None`:
  1. Loop `providers`
  2. Masing2 panggil `provider.fetch(ticker, period, need_profile)`
  3. Kalau return data: `cache.save(...)`, log info, return data
  4. Kalau exception/gagal: log warning, lanjut provider berikutnya
  5. Semua gagal: coba `cache.load_stale(...)`. Kalau ada: log warning "stale". Return.
  6. Gak ada cache: log error. Return None.
- `get_price(self, ticker)` — panggil provider pertama yang sukses (cache ga perlu untuk get_price)

**`get_provider()` function:**
- Parse `settings.provider_fallback_order` → list of provider names
- Ambil provider instances dari `_providers` dict
- Buat `FallbackProvider(providers, ProviderCache(ttl=settings.provider_cache_ttl_hours))`
- Return FallbackProvider

**Logging events:**
- `logger.info("FallbackProvider: {name} selected for {ticker}", name=..., ticker=...)`
- `logger.warning("FallbackProvider: {name} failed for {ticker}: {e}", ...)`
- `logger.warning("FallbackProvider: all failed, returning STALE cache for {ticker}", ...)`
- `logger.error("FallbackProvider: all failed, no cache for {ticker}", ...)`

---

### Task 5: Tests

**`tests/test_cache.py` — 3 test:**
1. `test_cache_save_load`: save, load, assert StockData match
2. `test_cache_miss`: load non-existent → None
3. `test_cache_expired`: save, set TTL = 0 (pake mock time atau langsung set file mtime), load → None

**`tests/test_fallback.py` — 3 test:**
1. `test_fallback_primary_success`: mock provider1 return data, provider2 never called. Assert FallbackProvider returns that data.
2. `test_fallback_to_secondary`: mock provider1 fail, provider2 return data. Assert FallbackProvider returns data dari provider2.
3. `test_fallback_all_fail_cached`: mock both fail, mock cache return data. Assert FallbackProvider returns cached data.
4. `test_fallback_all_fail_no_cache`: mock both fail, mock cache None. Assert FallbackProvider returns None.

---

### Task 6: Verify

```bash
pytest tests/test_cache.py tests/test_fallback.py tests/test_yahoo_finance.py tests/test_idx_provider.py -v
```

Expected: All pass. Gak ada test yg panggil Yahoo/IDX beneran.

```bash
pytest tests/ -v
```

Expected: All 73+ tests pass.
