from datetime import datetime, timezone
from uuid import uuid4

from pydantic import BaseModel


class WatchlistEntry(BaseModel):
    ticker: str
    added_at: str = ""
    position: int = 0


class Watchlist(BaseModel):
    id: str = ""
    name: str
    created_at: str = ""
    updated_at: str = ""
    entries: list[WatchlistEntry] = []

    def __init__(self, **data):
        super().__init__(**data)
        now = datetime.now(timezone.utc).isoformat()
        if not self.id:
            self.id = uuid4().hex[:12]
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = now
