#!/usr/bin/env bash
set -euo pipefail

python3 -m compileall kimibridge tests
python3 -m unittest discover -s tests

if [ "${1:-}" = "--binary" ] || [ "${BUILD_BINARY:-0}" = "1" ]; then
  python3 scripts/build_binary.py
fi
