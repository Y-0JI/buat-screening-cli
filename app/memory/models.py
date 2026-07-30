from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4


class MemoryType(str, Enum):
    USER_PREFERENCE = "user_preference"
    RESEARCH_FINDING = "research_finding"
    IMPORTANT_CONTEXT = "important_context"


@dataclass
class MemoryEntry:
    type: MemoryType
    content: str
    source: str | None = None
    id: str = field(default_factory=lambda: uuid4().hex[:12])
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
