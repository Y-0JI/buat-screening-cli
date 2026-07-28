from app.tools.base import Provider


class ProviderRegistry:
    _providers: dict[str, type[Provider]] = {}

    @classmethod
    def register(cls, name: str, provider_cls: type[Provider]) -> None:
        cls._providers[name] = provider_cls

    @classmethod
    def get(cls, name: str) -> type[Provider]:
        return cls._providers[name]

    @classmethod
    def all(cls) -> dict[str, type[Provider]]:
        return dict(cls._providers)
