from app.tools.registry import ProviderRegistry
from app.tools.yahoo_finance import YahooFinanceProvider
from app.tools.idx import IDXProvider
from app.config.settings import settings

registry = ProviderRegistry()
registry.register("yahoo", YahooFinanceProvider())
registry.register("idx", IDXProvider())

_default = settings.data_provider
if _default not in registry.list():
    _default = "yahoo"
registry.set_default(_default)


def get_provider(name: str | None = None) -> YahooFinanceProvider:
    return registry.get(name)
