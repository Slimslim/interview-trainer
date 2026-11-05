#!/usr/bin/env bash
# Deploy to GitHub Pages: rebuild packs + service worker, validate, push.
# The site is served from the gh-pages branch, which mirrors main.
set -euo pipefail
cd "$(dirname "$0")/.."
python3 tools/build.py
python3 tools/validate.py
if ! git diff --quiet; then git add -A && git commit -m "Build for deploy"; fi
git push origin main
git push origin main:gh-pages
echo "Deployed → https://slimslim.github.io/interview-trainer/ (live in ~1–3 min)"
