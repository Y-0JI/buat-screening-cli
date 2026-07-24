#!/usr/bin/env bash
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"
source .venv/bin/activate
pip install -e . > /dev/null 2>&1
"$DIR/.venv/bin/screening" info
echo ""
exec bash -i