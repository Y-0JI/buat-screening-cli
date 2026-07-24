from app.tools.registry import ProviderRegistry
from app.tools.yahoo_finance import YahooFinanceProvider

registry = ProviderRegistry()
registry.register("yahoo", YahooFinanceProvider(), default=True)


def get_provider(name: str | None = None) -> YahooFinanceProvider:
    return registry.get(name)
