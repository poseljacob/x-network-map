#!/usr/bin/env bash
# Build the map from the files in data/. Output: site/index.html
# Usage: ./run.sh            (uses python3)
#        PYTHON=.venv/bin/python ./run.sh
set -euo pipefail
cd "$(dirname "$0")"
PY="${PYTHON:-python3}"
"$PY" pipeline/prepare.py data
"$PY" pipeline/edges.py data
"$PY" pipeline/analyze.py data
"$PY" pipeline/layout.py data
"$PY" pipeline/build.py data site
echo "Done. Open site/index.html in a browser."
