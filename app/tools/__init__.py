from loguru import logger
from app.tools.yahoo_finance import YahooFinanceProvider
from app.tools.idx import IDXProvider
from app.tools.cache import ProviderCache
from app.config.settings import settings
from app.models.stock import StockData

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

    def fetch(self, ticker: str, period: str = "6mo", need_profile: bool = True) -> StockData | None:
        for provider in self.providers:
            name = type(provider).__name__
            try:
                data = provider.fetch(ticker, period, need_profile)
                if data:
                    logger.debug(f"{name}: success for {ticker}")
                    self.cache.save(ticker, period, need_profile, data)
                    return data
                logger.warning(f"{name}: no data for {ticker}")
            except Exception as e:
                logger.warning(f"{name}: failed for {ticker}: {e}")
        cached = self.cache.load(ticker, period, need_profile, allow_stale=True)
        if cached:
            logger.warning(f"All providers failed for {ticker}, returning stale cache")
            return cached
        logger.error(f"All providers failed for {ticker}, no cache available")
        return None

    def get_price(self, ticker: str) -> float | None:
        for provider in self.providers:
            try:
                price = provider.get_price(ticker)
                if price is not None:
                    return price
            except Exception:
                continue
        return None


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
