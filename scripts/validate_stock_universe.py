#!/usr/bin/env python3
"""Validate stock universe against data provider.

Reads app/data/idx_stocks.json, checks each ticker against Yahoo Finance,
adds sector info and validity flag. Writes result back.

Usage:
    python3 scripts/validate_stock_universe.py
"""

import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app.tools.yahoo_finance import YahooFinanceProvider
from app.tools.idx import IDXProvider

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "app", "data", "idx_stocks.json")
BATCH_SIZE = 3
BATCH_DELAY = 1.0


def main():
    provider = YahooFinanceProvider()

    with open(DATA_PATH) as f:
        stocks = json.load(f)

    total = len(stocks)
    validated = 0
    not_found = 0
    errors = 0

    for i, stock in enumerate(stocks):
        ticker = stock["ticker"]
        print(f"[{i+1}/{total}] {ticker}... ", end="", flush=True)

        try:
            data = provider.fetch(ticker, period="1mo")
            if data:
                sector = data.info.sector or ""
                stock["sector"] = sector
                stock["valid"] = True
                validated += 1
                print(f"OK sector={sector or '-'}")
            else:
                stock["sector"] = ""
                stock["valid"] = False
                not_found += 1
                print("NOT_FOUND")
        except Exception as e:
            stock["sector"] = ""
            stock["valid"] = False
            errors += 1
            print(f"ERROR {e}")

        if (i + 1) % BATCH_SIZE == 0 and i + 1 < total:
            time.sleep(BATCH_DELAY)

    with open(DATA_PATH, "w") as f:
        json.dump(stocks, f, indent=2)

    print(f"\nDone: {validated} valid, {not_found} not found, {errors} errors (total {total})")


if __name__ == "__main__":
    main()
