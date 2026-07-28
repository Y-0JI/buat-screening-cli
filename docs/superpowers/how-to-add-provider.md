# Cara Tambah Provider Data Baru

## Prasyarat

- Paham Python 3.10+
- Paham model `StockData`, `StockInfo`, `HistoricalPrice`, `SymbolInfo`
- Paham cara data provider bekerja (fetch harga saham, listing symbols)

## Langkah-langkah

### 1. Buat file baru di `app/tools/`

Contoh: `app/tools/finnhub_provider.py`

### 2. Import base class dan registry

```python
from app.tools.base import Provider
from app.tools.registry import ProviderRegistry
from app.models.stock import StockData, StockInfo, HistoricalPrice
from app.models.symbol import SymbolInfo
```

### 3. Buat class yang extends `Provider`

```python
class FinnhubProvider(Provider):
    def fetch(self, ticker: str, **kwargs) -> StockData | None:
        # period, need_profile dll bisa diambil dari kwargs
        period = kwargs.get("period", "6mo")
        # ... implementasi fetch data ...
        return StockData(info=..., history=[...])

    def get_price(self, ticker: str) -> float | None:
        # ... ambil harga terkini ...
        return 1000.0

    def list_symbols(self) -> list[SymbolInfo]:
        # ... listing saham yang tersedia ...
        return []
```

Method yang wajib diimplementasikan:
- `fetch(ticker, **kwargs) -> StockData | None` — ambil data historis
- `get_price(ticker) -> float | None` — ambil harga terkini
- `list_symbols() -> list[SymbolInfo]` — daftar symbol yang tersedia

### 4. Daftarkan provider ke registry

Letakkan di module level setelah class definition:

```python
ProviderRegistry.register("finnhub", FinnhubProvider)
```

### 5. Tambah ke konfigurasi

Edit `.env` atau environment variable:

```env
provider_fallback_order=yahoo,idx,finnhub
```

## Selesai

Tidak perlu mengubah:
- `app/tools/__init__.py` — otomatis baca dari registry
- `app/router/engine.py` — tidak tahu provider mana yang dipakai
- `app/cli/main.py` — tidak tahu provider mana yang dipakai
- `app/tools/cache.py` — sudah generic

## Verifikasi

```bash
# Cek provider terdaftar
python3 -c "from app.tools.registry import ProviderRegistry; print(ProviderRegistry.all())"

# Test fallback masih jalan
pytest tests/test_fallback.py -v
```
