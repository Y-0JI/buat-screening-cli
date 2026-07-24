from app.tools.base import StockProvider


class ProviderRegistry:
    def __init__(self):
        self._providers: dict[str, StockProvider] = {}
        self._default: str | None = None

    def register(self, name: str, provider: StockProvider, default: bool = False):
        self._providers[name] = provider
        if default or self._default is None:
            self._default = name

    def get(self, name: str | None = None) -> StockProvider:
        key = name or self._default
        if key is None:
            raise ValueError("No provider registered")
        return self._providers[key]

    def set_default(self, name: str) -> None:
        if name not in self._providers:
            raise ValueError(f"Provider '{name}' not registered. Available: {list(self._providers)}")
        self._default = name

    def list(self) -> dict[str, StockProvider]:
        return dict(self._providers)
