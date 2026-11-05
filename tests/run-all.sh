#!/usr/bin/env bash
# Runs every definition-of-done check. Usage: bash tests/run-all.sh
set -euo pipefail
cd "$(dirname "$0")/.."
python3 tools/build.py            # packs + service-worker manifest
python3 tools/validate.py         # schema, research sources, CPython execution checks
node tools/validate-pyodide.mjs   # same execution checks inside Pyodide
node tests/e2e.mjs                # iPhone 15: UX, offline, performance, progress, AI coach
