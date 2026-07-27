# Phase 1 — Stabilize Data Providers

## Objective

Ensure the application always retrieves stock data reliably by adding automatic provider fallback, retry for IDX provider, and disk-based caching of successful responses.

## Scope

- **Auto-fallback**: When primary provider fails, try secondary provider transparently
- **Retry IDX**: Add retry logic to IDXProvider (matching YahooFinanceProvider pattern)
- **Disk cache**: Save successful StockData responses. Return cached data when all providers fail.
- **Config**: Provider order + cache TTL configurable via `.env`
- **Logging**: Log provider selection, retries, fallback events, cache hits/misses

## Not in Scope

- Dynamic symbol discovery (Phase 2+)
- Replacing static idx_stocks.json
- Provider architecture redesign (Phase 6)
- validate_universe.py changes

## Architecture

### Components

**ProviderCache** (`app/tools/cache.py`):
- Simple file-based cache
- Key = hash of `{ticker}:{period}:{need_profile}`
- Value = StockData as JSON via Pydantic serialization
- TTL checked via file mtime
- Returns None if no cache or TTL expired
- Provider-agnostic — same cache for all providers

**FallbackProvider** (`app/tools/__init__.py`):
- Wraps list of providers in priority order
- `fetch()` iterates providers, returns first success
- On all-fail: tries cache before returning None
- Same interface as individual providers — no downstream changes needed

**IDXProvider retry** (`app/tools/idx.py`):
- 3 attempts with 1s, 2s backoff
- Same error classification pattern as YahooFinanceProvider

### Data Flow

```
fetch(ticker) →
  FallbackProvider.fetch(ticker) →
    Provider1.fetch(ticker) → success → cache.save() → return
    Provider1.fetch(ticker) → fail →
    Provider2.fetch(ticker) → success → cache.save() → return
    Semua fail → cache.load() → hit → return cached (warning stale)
    Semua fail → cache.load() → miss → return None (error)
```

### Config (.env)

```
PROVIDER_FALLBACK_ORDER=yahoo,idx
PROVIDER_CACHE_TTL_HOURS=24
```
