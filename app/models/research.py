from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

REPORT_SECTIONS = (
    "executive_summary",
    "market",
    "company",
    "price",
    "technical",
    "risk",
    "fundamental",
    "financial",
    "valuation",
    "growth",
    "dividend",
    "market_intelligence",
    "investment_conclusion",
)

SCHEMA_VERSION = 1


class SectionStatus(str, Enum):
    AVAILABLE = "available"
    PARTIAL = "partial"
    MISSING = "missing"


@dataclass(frozen=True)
class ResearchSection:
    source: str = ""
    status: SectionStatus = SectionStatus.MISSING
    data: dict = field(default_factory=dict)


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
