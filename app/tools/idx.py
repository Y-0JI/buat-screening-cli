from datetime import date, datetime, timedelta
import httpx
from loguru import logger
from app.models.stock import HistoricalPrice, StockData, StockInfo
from app.tools.base import StockProvider

_BROWSER_HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9,id;q=0.8",
    "Referer": "https://www.idx.co.id/",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
}


class IDXProvider(StockProvider):
    def __init__(self):
        self._client: httpx.Client | None = None

    def _ensure_session(self):
        if self._client is not None:
            return
        client = httpx.Client(headers=_BROWSER_HEADERS, follow_redirects=True)
        client.get("https://www.idx.co.id/id")
        client.get("https://www.idx.co.id/primary/home/GetIndexList")
        self._client = client

    def fetch(self, ticker: str, period: str = "6mo") -> StockData | None:
        self._ensure_session()
        try:
            raw = self._client.get(
                "https://www.idx.co.id/primary/ListedCompany/GetTradingInfoSS",
                params={"code": ticker, "start": 0, "length": 1000},
            ).json()
            if not raw or not raw.get("replies"):
                logger.info(f"Data kosong untuk {ticker}")
                return None
            replies = raw["replies"]
            history = []
            cutoff = _parse_period(period)
            for r in replies:
                d = _parse_date(r.get("Date", ""))
                if not d:
                    continue
                if cutoff and d < cutoff:
                    continue
                history.append(HistoricalPrice(
                    date=d,
                    open=float(r.get("OpenPrice", 0)),
                    high=float(r.get("High", 0)),
                    low=float(r.get("Low", 0)),
                    close=float(r.get("Close", 0)),
                    volume=int(r.get("Volume", 0)),
                ))
            if not history:
                return None
            history.sort(key=lambda h: h.date)
            meta = self._fetch_meta(ticker)
            return StockData(
                info=StockInfo(
                    ticker=ticker.upper(),
                    name=meta.get("name", ticker.upper()),
                    sector=meta.get("sector"),
                ),
                history=history,
            )
        except Exception as e:
            logger.warning(f"Gagal fetch IDX {ticker}: {e}")
            return None

    def get_price(self, ticker: str) -> float | None:
        self._ensure_session()
        try:
            raw = self._client.get(
                "https://www.idx.co.id/primary/ListedCompany/GetTradingInfoDaily",
                params={"code": ticker},
            ).json()
            if raw and raw.get("ClosingPrice"):
                return float(raw["ClosingPrice"])
        except Exception as e:
            logger.warning(f"Gagal get_price IDX {ticker}: {e}")
        return None

    def _fetch_meta(self, ticker: str) -> dict:
        try:
            raw = self._client.get(
                "https://www.idx.co.id/primary/ListedCompany/GetCompanyProfilesDetail",
                params={"KodeEmiten": ticker, "language": "id-id"},
            ).json()
            if raw and raw.get("Profiles") and len(raw["Profiles"]) > 0:
                p = raw["Profiles"][0]
                return {"name": p.get("NamaEmiten", ""), "sector": p.get("Sektor")}
        except Exception:
            pass
        return {}


def _parse_date(s: str) -> date | None:
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%d/%m/%Y", "%Y%m%d"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def _parse_period(period: str) -> date | None:
    if period in ("max", None, ""):
        return None
    unit = period[-2:]
    try:
        n = int(period[:-2])
    except ValueError:
        return None
    today = date.today()
    if unit == "mo":
        return today - timedelta(days=n * 30)  # ponytail: ~30d month, fine for indicator window
    if unit == "d":
        return today - timedelta(days=n)
    if unit == "y":
        return today - timedelta(days=n * 365)
    if unit == "wk":
        return today - timedelta(weeks=n)
    return None
