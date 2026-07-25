from abc import ABC, abstractmethod


class BasePresenter(ABC):
    @abstractmethod
    def analysis(self, analysis) -> None: ...

    @abstractmethod
    def research_report(self, report) -> None: ...

    @abstractmethod
    def error(self, message: str) -> None: ...

    @abstractmethod
    def info(self, message: str) -> None: ...

    @abstractmethod
    def table(self, title: str, columns: list[tuple[str, str]], rows: list[list[str]]) -> None: ...

    @abstractmethod
    def stock_header(self, data) -> None: ...
