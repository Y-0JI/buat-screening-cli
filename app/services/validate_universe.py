import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

import yfinance as yf

from app.tools.yahoo_finance import _last_rate_limit, _RATE_LIMITED_PATTERNS

_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "idx_stocks.json")
_TIMESTAMP_PATH = os.path.join(os.path.dirname(__file__), "..", "data", ".universe_validated")
_BATCH_SIZE = 50


def _check(ticker: str) -> tuple[str, str]:
    cooldown = time.time() - _last_rate_limit[0]
    if cooldown < 15:
        time.sleep(15 - cooldown)
    try:
        hist = yf.download(ticker + ".JK", period="1d", progress=False)
        if not hist.empty:
            return ticker, "valid"
        return ticker, "not_found"
    except Exception as e:
        msg = str(e).lower()
        for pat in _RATE_LIMITED_PATTERNS:
            if pat in msg:
                _last_rate_limit[0] = time.time()
                return ticker, "rate_limited"
        if "delisted" in msg or "no price data found" in msg:
            return ticker, "not_found"
        return ticker, "error"


def _save(stocks: list[dict]) -> None:
    with open(_DATA_PATH, "w") as f:
        json.dump(stocks, f, indent=2)


def _write_timestamp() -> None:
    with open(_TIMESTAMP_PATH, "w") as f:
        f.write(datetime.now(timezone.utc).isoformat())


def last_validated_days() -> int | None:
    try:
        mtime = os.path.getmtime(_TIMESTAMP_PATH)
        return int((time.time() - mtime) / 86400)
    except FileNotFoundError:
        return None


def run(dry_run: bool = False) -> None:
    with open(_DATA_PATH) as f:
        stocks = json.load(f)

    tickers = [s["ticker"] for s in stocks]
    total = len(tickers)
    stocks_by_ticker = {s["ticker"]: s for s in stocks}
    changed = 0
    done = 0
    summary = {"valid": 0, "not_found": 0, "rate_limited": 0, "error": 0}

    print(f"Memvalidasi {total} ticker...", file=sys.stderr)

    try:
        with ThreadPoolExecutor(max_workers=2) as ex:
            futures = {ex.submit(_check, t): t for t in tickers}
            for f in as_completed(futures):
                ticker, status = f.result()
                entry = stocks_by_ticker[ticker]
                old = entry.get("valid", True)
                summary[status] += 1

                if status == "not_found" and old is not False:
                    entry["valid"] = False
                    changed += 1
                elif status == "valid" and old is not True:
                    entry["valid"] = True
                    changed += 1

                done += 1
                if done % 100 == 0:
                    print(f"  {done}/{total}", file=sys.stderr)
                if done % _BATCH_SIZE == 0 and not dry_run:
                    _save(list(stocks_by_ticker.values()))
    except KeyboardInterrupt:
        if not dry_run:
            _save(list(stocks_by_ticker.values()))
        print(file=sys.stderr)
        print(f"Diinterupsi. {done} ticker selesai.", file=sys.stderr)
        return

    if not dry_run:
        _save(list(stocks_by_ticker.values()))
        _write_timestamp()

    valid_count = summary["valid"]
    invalid_count = summary["not_found"]
    print(
        f"\nSelesai. {total} ticker: {valid_count} valid, {invalid_count} not_found, "
        f"{summary['rate_limited']} rate_limited, {summary['error']} error, {changed} berubah.",
        file=sys.stderr,
    )
