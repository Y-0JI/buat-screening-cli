# PERBAIKAN_11 — Peningkatan Kualitas Stock Universe

## Masalah
Stock universe berisi ticker yang sudah tidak valid/tidak dapat diproses provider.
Setiap bulk screening tetap memproses semua ticker termasuk yang invalid,
menghasilkan request tidak bernilai dan beban tambahan.

## Perubahan

### `scripts/validate_stock_universe.py`
Script standalone untuk memvalidasi stock universe terhadap data provider.
Membaca `app/data/idx_stocks.json`, mengecek tiap ticker via `provider.fetch()`,
menambahkan `sector` dan `valid` flag. Menulis hasil kembali ke file yang sama.

Usage: `python3 scripts/validate_stock_universe.py`

### `app/services/stock_list.py`
- `get_all()`: filter hanya ticker dengan `valid=True` jika field `valid` ada
- `search()`: sama — hasil pencarian difilter
- `count()`: menggunakan `get_all()` untuk akurasi

### `app/data/idx_stocks.json`
Sekarang berisi field tambahan `sector` (string) dan `valid` (bool) per ticker.

### Tidak diubah
- Business logic screening
- AI analysis
- CLI/formatter/output
- Request orchestration
