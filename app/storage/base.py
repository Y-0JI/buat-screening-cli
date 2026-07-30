from abc import ABC, abstractmethod


class StorageBackend(ABC):
    @abstractmethod
    def load(self) -> list[dict]: ...

    @abstractmethod
    def save(self, data: list[dict]) -> None: ...
