from app.tools.yahoo_finance import YahooFinanceProvider
from app.tools.idx import IDXProvider
from app.config.settings import settings

_providers = {"yahoo": YahooFinanceProvider(), "idx": IDXProvider()}
_default = settings.data_provider if settings.data_provider in _providers else "yahoo"


def get_provider(name: str | None = None):
    return _providers[name or _default]
