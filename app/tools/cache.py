import json
import os
import time
from pathlib import Path
from loguru import logger
from app.models.stock import StockData
from app.validation import normalize

_CACHE_DIR = Path(__file__).parent.parent / "data" / "provider_cache"


class ProviderCache:
    def __init__(self, cache_dir: str | Path = _CACHE_DIR, ttl_hours: int = 24):
        self.cache_dir = Path(cache_dir)
        self.ttl_seconds = ttl_hours * 3600
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _is_expired(self, path: Path, ttl_hours: float | None = None) -> bool:
        ttl = (ttl_hours if ttl_hours is not None else self.ttl_seconds / 3600) * 3600
        return time.time() - os.path.getmtime(path) > ttl

    def save_json(self, key: str, data: dict) -> None:
        path = self.cache_dir / f"{key}.json"
        try:
            path.write_text(json.dumps(data))
            logger.debug(f"JSON cache SAVED: {key}")
        except Exception as e:
            logger.warning(f"JSON cache SAVE failed: {key}: {e}")

    def load_json(self, key: str, ttl_hours: float | None = None) -> dict | None:
        path = self.cache_dir / f"{key}.json"
        if not path.exists():
            logger.debug(f"JSON cache MISS: {key}")
            return None
        if self._is_expired(path, ttl_hours):
            logger.debug(f"JSON cache EXPIRED: {key}")
            return None
        try:
            data = json.loads(path.read_text())
            logger.debug(f"JSON cache HIT: {key}")
            return data
        except Exception as e:
            logger.warning(f"JSON cache LOAD failed: {key}: {e}")
            return None

    def _path(self, ticker: str, period: str, need_profile: bool) -> Path:
        safe = f"{normalize(ticker)}_{period}_{need_profile}"
        return self.cache_dir / f"{safe}.json"

    def save(self, ticker: str, period: str, need_profile: bool, data: StockData) -> None:
        path = self._path(ticker, period, need_profile)
        try:
            path.write_text(data.model_dump_json())
            logger.debug(f"Cache SAVED: {ticker} ({period})")
        except Exception as e:
            logger.warning(f"Cache SAVE failed: {ticker}: {e}")

    def load(self, ticker: str, period: str, need_profile: bool, allow_stale: bool = False) -> StockData | None:
        path = self._path(ticker, period, need_profile)
        if not path.exists():
            logger.debug(f"Cache MISS: {ticker}")
            return None
        if not allow_stale:
            if self._is_expired(path):
                logger.debug(f"Cache EXPIRED: {ticker}")
                return None
        try:
            data = StockData.model_validate_json(path.read_text())
            if allow_stale:
                logger.warning(f"Cache STALE: {ticker}")
            else:
                logger.debug(f"Cache HIT: {ticker}")
            return data
        except Exception as e:
            logger.warning(f"Cache LOAD failed: {ticker}: {e}")
            return None
