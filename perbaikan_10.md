# PERBAIKAN_10 — Bulk Screening Rate Limit Strategy

## Masalah

Bulk screening masih sering gagal ketika provider menerapkan rate limit.

Retry sudah diimplementasikan, tetapi setiap worker melakukan retry secara independen sehingga banyak request dikirim kembali pada waktu yang hampir bersamaan. Akibatnya rate limit tetap terjadi walaupun sudah ada mekanisme retry.

## Perubahan

### `router/engine.py`
- `_fetch_and_screen()`: spread start time concurrent request dengan `time.sleep(random.uniform(0, 0.15))` agar worker tidak mulai bersamaan.
- `_fetch_with_stagger()`: wrapper baru untuk `bulk_gainers()`/`bulk_losers()` dengan spread yang sama.
- `bulk_gainers()`/`bulk_losers()`: pakai `_fetch_with_stagger()` instead of langsung `provider.fetch()`.

### `yahoo_finance.py`
- Retry backoff `time.sleep(1 + attempt)` → `time.sleep((1 + attempt) * random.uniform(0.5, 1.5))`. Jitter mendesinkronisasi retry antar worker tanpa mengubah average delay.

### Tidak diubah
- Business logic screening
- Jumlah retry (tetap max 3)
- Interface CLI
- Formatter output
- Stock universe
