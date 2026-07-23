from dataclasses import dataclass, field
from app.models.stock import StockData
from app.screeners.engine import ScreeningResult


@dataclass
class AIAnalysis:
    ticker: str
    summary: str
    key_metrics: dict[str, str | float] = field(default_factory=dict)
    risks: list[str] = field(default_factory=list)
    conclusion: str = ""
    raw_data: StockData | None = None
    screening_results: list[ScreeningResult] | None = None
