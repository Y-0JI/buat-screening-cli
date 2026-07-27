import hashlib
import json
import os
import time
from pathlib import Path
from loguru import logger
from app.models.stock import StockData

_CACHE_DIR = Path(__file__).parent.parent / "data" / "provider_cache"


class ProviderCache:
    def __init__(self, cache_dir: str | Path = _CACHE_DIR, ttl_hours: int = 24):
        self.cache_dir = Path(cache_dir)
        self.ttl_seconds = ttl_hours * 3600
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _key(self, ticker: str, period: str, need_profile: bool) -> str:
        raw = f"{ticker.upper()}:{period}:{need_profile}"
        return hashlib.md5(raw.encode()).hexdigest()[:16]

    def _path(self, key: str) -> Path:
        return self.cache_dir / f"{key}.json"

    def save(self, ticker: str, period: str, need_profile: bool, data: StockData) -> None:
        key = self._key(ticker, period, need_profile)
        path = self._path(key)
        try:
            path.write_text(data.model_dump_json())
            logger.debug(f"Cache SAVED: {key} ({ticker})")
        except Exception as e:
            logger.warning(f"Cache SAVE failed: {key}: {e}")

    def load(self, ticker: str, period: str, need_profile: bool) -> StockData | None:
        key = self._key(ticker, period, need_profile)
        path = self._path(key)
        if not path.exists():
            logger.debug(f"Cache MISS: {key}")
            return None
        age = time.time() - os.path.getmtime(path)
        if age > self.ttl_seconds:
            logger.debug(f"Cache EXPIRED: {key}, age={age/3600:.1f}h")
            return None
        try:
            data = StockData.model_validate_json(path.read_text())
            logger.debug(f"Cache HIT: {key} ({ticker})")
            return data
        except Exception as e:
            logger.warning(f"Cache LOAD failed: {key}: {e}")
            return None

    def load_stale(self, ticker: str, period: str, need_profile: bool) -> StockData | None:
        key = self._key(ticker, period, need_profile)
        path = self._path(key)
        if not path.exists():
            return None
        try:
            data = StockData.model_validate_json(path.read_text())
            logger.warning(f"Cache STALE: {key} ({ticker})")
            return data
        except Exception:
            return None
