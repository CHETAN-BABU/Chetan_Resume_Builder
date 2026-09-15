#!/bin/bash
# Starts the whole local application: Python API, shared database and React client.
set -euo pipefail
export PATH="/opt/homebrew/bin:/usr/local/bin:$HOME/Library/pnpm:$PATH"
cd "$(dirname "$0")"
if ! command -v python3 >/dev/null; then
  echo "Python 3 is required. Install it (for example 'brew install python') and try again." >&2
  exit 1
fi
if [ ! -x .venv/bin/python ]; then
  python3 -m venv .venv
  .venv/bin/python -m pip install --quiet --upgrade pip
  .venv/bin/python -m pip install -r requirements.txt
fi
# The dashboard itself does not need the PDF toolchain; resume builds report it when missing.
export RESUME_RUNTIME_OPTIONAL=1
exec .venv/bin/python ../daily-job-search/with_resume_runtime.py .venv/bin/python dashboard/run.py "$@"
