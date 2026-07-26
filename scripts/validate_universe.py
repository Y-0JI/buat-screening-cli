#!/usr/bin/env python3
"""Parallel validation of idx_stocks.json via Yahoo Finance.

Usage: python scripts/validate_universe.py

Updates valid=true/false for each ticker based on whether
yfinance can find price data for it. Delisted tickers get valid=false
so get_all() skips them during bulk screening.
"""

import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

import yfinance as yf

_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "app", "data", "idx_stocks.json")


def _check(ticker: str) -> tuple[str, bool]:
    try:
        hist = yf.download(ticker + ".JK", period="1d", progress=False)
        return ticker, not hist.empty
    except Exception:
        return ticker, False


def main():
    with open(_DATA_PATH) as f:
        stocks = json.load(f)

    tickers = [s["ticker"] for s in stocks]
    total = len(tickers)
    changed = 0
    done = 0

    print(f"Validating {total} tickers...", file=sys.stderr)

    with ThreadPoolExecutor(max_workers=10) as ex:
        futures = {ex.submit(_check, t): i for i, t in enumerate(tickers)}
        for f in as_completed(futures):
            i = futures[f]
            ticker, valid = f.result()
            old = stocks[i].get("valid", True)
            if old != valid:
                stocks[i]["valid"] = valid
                changed += 1
            done += 1
            if done % 100 == 0:
                print(f"  {done}/{total}", file=sys.stderr)

    with open(_DATA_PATH, "w") as f:
        json.dump(stocks, f, indent=2)

    valid_count = sum(1 for s in stocks if s.get("valid", True))
    invalid_count = total - valid_count
    print(
        f"\nDone. {total} tickers: {valid_count} valid, {invalid_count} invalid, {changed} changed.",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
