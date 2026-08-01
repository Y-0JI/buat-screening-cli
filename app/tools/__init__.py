from loguru import logger
from app.tools.base import _classify_error
from app.tools.cache import ProviderCache
from app.tools.registry import ProviderRegistry
from app.config.settings import settings
from app.models.stock import StockData
from app.models.symbol import SymbolInfo
from app.validation import is_valid, normalize

# side-effect imports: triggers ProviderRegistry.register() in each module
import app.tools.yahoo_finance  # noqa: F401
import app.tools.idx  # noqa: F401


class FallbackProvider:
    def __init__(self, providers: list, cache: ProviderCache):
        self.providers = providers
        self.cache = cache
        self._stats: dict[str, dict] = {}
        for p in providers:
            self._stats[type(p).__name__] = {"ok": 0, "fail": 0, "rate_limited": 0, "not_found": 0, "error": 0}

    def fetch(self, ticker: str, period: str = "6mo", need_profile: bool = True) -> StockData | None:
        ticker = normalize(ticker)
        if not is_valid(ticker):
            logger.warning(f"Invalid symbol rejected: {ticker}")
            return None
        cached = self.cache.load(ticker, period, need_profile)
        if cached:
            logger.debug(f"Fresh cache HIT: {ticker} ({period}) — skipping provider")
            return cached
        for provider in self.providers:
            name = type(provider).__name__
            try:
                data = provider.fetch(ticker, period, need_profile)
                if data:
                    logger.debug(f"{name}: success for {ticker}")
                    self.cache.save(ticker, period, need_profile, data)
                    self._stats[name]["ok"] += 1
                    return data
                logger.warning(f"{name}: no data for {ticker}")
                self._stats[name]["fail"] += 1
            except Exception as e:
                kind = _classify_error(e)
                logger.warning(f"{name}: {kind} for {ticker}: {e}")
                self._stats[name][kind] += 1
        cached = self.cache.load(ticker, period, need_profile, allow_stale=True)
        if cached:
            logger.warning(f"All providers failed for {ticker}, returning stale cache")
            return cached
        logger.warning(f"All providers failed for {ticker}, no cache available")
        return None

    def health_summary(self) -> str:
        lines = []
        for name, c in self._stats.items():
            parts = [f"ok={c['ok']}", f"fail={c['fail']}", f"rate_limited={c['rate_limited']}"]
            if c.get("not_found"):
                parts.append(f"not_found={c['not_found']}")
            if c.get("error"):
                parts.append(f"error={c['error']}")
            lines.append(f"{name}: {', '.join(parts)}")
        return "\n".join(lines)

    def get_price(self, ticker: str) -> float | None:
        ticker = normalize(ticker)
        if not is_valid(ticker):
            return None
        for provider in self.providers:
            try:
                price = provider.get_price(ticker)
                if price is not None:
                    return price
            except Exception:
                continue
        return None

    def list_symbols(self) -> list[SymbolInfo]:
        results = []
        for provider in self.providers:
            try:
                results.extend(provider.list_symbols())
            except Exception:
                logger.warning(f"list_symbols gagal untuk {type(provider).__name__}, dilewati")
        return results


def get_provider(name: str | None = None):
    if name:
        return ProviderRegistry.get(name)()
    order = settings.provider_fallback_order.split(",")
    all_p = ProviderRegistry.all()
    ordered = [p.strip() for p in order if p.strip() in all_p]
    if not ordered:
        ordered = [list(all_p.keys())[0]]
    providers = [all_p[p]() for p in ordered]
    cache = ProviderCache(ttl_hours=settings.provider_cache_ttl_hours)
    return FallbackProvider(providers, cache)
