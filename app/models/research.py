from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

REPORT_SECTIONS = (
    "executive_summary",
    "market",
    "company",
    "price",
    "technical",
    "comparison",
    "risk",
    "fundamental",
    "financial",
    "valuation",
    "growth",
    "dividend",
    "market_intelligence",
    "investment_conclusion",
)

REPORT_SECTION_LABELS = {
    "executive_summary": "Ringkasan Eksekutif",
    "market": "Market Overview",
    "company": "Company Overview",
    "price": "Price Analysis",
    "technical": "Technical Analysis",
    "comparison": "Comparison",
    "risk": "Risk Assessment",
    "fundamental": "Fundamental Analysis",
    "financial": "Financial Analysis",
    "valuation": "Valuation",
    "growth": "Growth",
    "dividend": "Dividend",
    "market_intelligence": "Market Intelligence",
    "investment_conclusion": "Investment Conclusion",
}

SCHEMA_VERSION = 1

REASON_NEWS_UNAVAILABLE = "news_unavailable"
REASON_FINANCIALS_UNAVAILABLE = "financials_unavailable"
REASON_NO_MARKET_CONTEXT = "no_market_context"


class SectionStatus(str, Enum):
    AVAILABLE = "available"
    PARTIAL = "partial"
    MISSING = "missing"


@dataclass(frozen=True)
class ResearchSection:
    source: str = ""
    status: SectionStatus = SectionStatus.MISSING
    data: dict = field(default_factory=dict)
    reason: str = ""


@dataclass(frozen=True)
class ResearchData:
    """Contract between research tools and report generator.

    Provider-independent: every tool fills the same schema. Report generator
    only reads. Immutable after normalization (frozen) — downstream code
    cannot mutate the contract.
    """

    schema_version: int = SCHEMA_VERSION
    symbol: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    sections: dict[str, ResearchSection] = field(default_factory=dict)
