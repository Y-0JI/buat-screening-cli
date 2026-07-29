import time
from datetime import date, datetime, timedelta
from curl_cffi import requests as curl_requests
from loguru import logger
from app.models.stock import HistoricalPrice, StockData, StockInfo
from app.models.symbol import SymbolInfo
from app.tools.base import Provider
from app.tools.registry import ProviderRegistry

_BROWSER_HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9,id;q=0.8",
    "Referer": "https://www.idx.co.id/",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest",
}


class IDXProvider(Provider):
    def __init__(self):
        self._session: curl_requests.Session | None = None

    def _ensure_session(self):
        if self._session is not None:
            return
        session = curl_requests.Session()
        session.headers.update(_BROWSER_HEADERS)
        session.get("https://www.idx.co.id/id", impersonate="chrome131")
        time.sleep(1)
        session.get("https://www.idx.co.id/primary/home/GetIndexList", impersonate="chrome131")
        self._session = session

    def fetch(self, ticker: str, period: str = "6mo", need_profile: bool = True) -> StockData | None:
        self._ensure_session()
        for attempt in range(3):
            try:
                raw = self._session.get(
                    "https://www.idx.co.id/primary/ListedCompany/GetTradingInfoSS",
                    params={"code": ticker, "start": 0, "length": 1000},
                    impersonate="chrome131",
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
                if attempt < 2:
                    delay = min(1000 * 2 ** attempt, 15000) / 1000
                    logger.debug(f"Retry IDX {ticker} in {delay}s (attempt {attempt+1}/3): {e}")
                    time.sleep(delay)
                else:
                    logger.warning(f"Gagal fetch IDX {ticker} setelah 3 percobaan: {e}")
        return None

    def get_price(self, ticker: str) -> float | None:
        self._ensure_session()
        try:
            raw = self._session.get(
                "https://www.idx.co.id/primary/ListedCompany/GetTradingInfoDaily",
                params={"code": ticker},
                impersonate="chrome131",
            ).json()
            if raw and raw.get("ClosingPrice"):
                return float(raw["ClosingPrice"])
        except Exception as e:
            logger.warning(f"Gagal get_price IDX {ticker}: {e}")
        return None

    def _fetch_meta(self, ticker: str) -> dict:
        try:
            raw = self._session.get(
                "https://www.idx.co.id/primary/ListedCompany/GetCompanyProfilesDetail",
                params={"KodeEmiten": ticker, "language": "id-id"},
                impersonate="chrome131",
            ).json()
            if raw and raw.get("Profiles") and len(raw["Profiles"]) > 0:
                p = raw["Profiles"][0]
                return {"name": p.get("NamaEmiten", ""), "sector": p.get("Sektor")}
        except Exception:
            pass
        return {}

    def list_symbols(self) -> list[SymbolInfo]:
        self._ensure_session()
        try:
            raw = self._session.get(
                "https://www.idx.co.id/primary/ListedCompany/GetStockList",
                impersonate="chrome131",
            ).json()
            if not raw:
                return []
            result = []
            for item in raw:
                result.append(SymbolInfo(
                    ticker=item.get("KodeEmiten", ""),
                    name=item.get("NamaEmiten"),
                    sector=item.get("Sektor"),
                ))
            return result
        except Exception as e:
            logger.warning(f"IDX: gagal ambil daftar emiten via API: {e}")
            logger.warning("IDX: endpoint mungkin diblokir Cloudflare atau tidak tersedia. Pakai fallback discovery provider lain atau file statis.")
            return []


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
        return today - timedelta(days=n * 30)
    if unit == "d":
        return today - timedelta(days=n)
    if unit == "y":
        return today - timedelta(days=n * 365)
    if unit == "wk":
        return today - timedelta(weeks=n)
    return None


ProviderRegistry.register("idx", IDXProvider)
