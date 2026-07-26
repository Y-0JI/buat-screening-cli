#!/usr/bin/env python3
"""CLI entry point for validate-universe.

Usage: python scripts/validate_universe.py
       python scripts/validate_universe.py --dry-run
"""

import sys

from app.services.validate_universe import run

if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    run(dry_run=dry_run)
