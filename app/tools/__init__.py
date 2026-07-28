from loguru import logger
from app.tools.yahoo_finance import YahooFinanceProvider
from app.tools.idx import IDXProvider
from app.tools.cache import ProviderCache
from app.config.settings import settings
from app.models.stock import StockData
from app.models.symbol import SymbolInfo
from app.validation import is_valid, normalize

_providers = {
    "yahoo": YahooFinanceProvider(),
    "idx": IDXProvider(),
}

_default = settings.data_provider
if _default not in _providers:
    _default = "yahoo"


class FallbackProvider:
    def __init__(self, providers: list, cache: ProviderCache):
        self.providers = providers
        self.cache = cache
        self._stats: dict[str, dict] = {}
        for p in providers:
            self._stats[type(p).__name__] = {"ok": 0, "fail": 0, "rate_limited": 0}

    def fetch(self, ticker: str, period: str = "6mo", need_profile: bool = True) -> StockData | None:
        ticker = normalize(ticker)
        if not is_valid(ticker):
            logger.warning(f"Invalid symbol rejected: {ticker}")
            return None
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
                logger.warning(f"{name}: failed for {ticker}: {e}")
                self._stats[name]["rate_limited"] += 1
        cached = self.cache.load(ticker, period, need_profile, allow_stale=True)
        if cached:
            logger.warning(f"All providers failed for {ticker}, returning stale cache")
            return cached
        logger.error(f"All providers failed for {ticker}, no cache available")
        return None

    def health_summary(self) -> str:
        lines = []
        for name, c in self._stats.items():
            lines.append(f"{name}: ok={c['ok']}, fail={c['fail']}, rate_limited={c['rate_limited']}")
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
            results.extend(provider.list_symbols())
        return results


def get_provider(name: str | None = None):
    if name:
        return _providers[name]
    order = settings.provider_fallback_order.split(",")
    ordered = [p.strip() for p in order if p.strip() in _providers]
    if not ordered:
        ordered = [_default]
    providers = [_providers[p] for p in ordered]
    cache = ProviderCache(ttl_hours=settings.provider_cache_ttl_hours)
    return FallbackProvider(providers, cache)
