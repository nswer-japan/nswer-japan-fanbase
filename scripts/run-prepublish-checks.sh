#!/usr/bin/env bash
set -euo pipefail
python3 scripts/build-content.py
python3 scripts/validate-site.py
python3 scripts/check-site-links.py
for file in js/*.js data/*-data.js service-worker.js; do node --check "$file"; done
for file in scripts/*.mjs; do node --check "$file"; done
python3 -m compileall -q scripts
python3 scripts/test-youtube-sync.py
printf '公開前検査に合格しました。\n'
