#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/career-dashboard"
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
.venv/bin/python ../daily-job-search/with_resume_runtime.py .venv/bin/python -m pytest tests -q
.venv/bin/python scripts/validate_workspace.py
.venv/bin/python scripts/check_layout.py

.venv/bin/python scripts/build_frontend.py
NODE_BIN="$(command -v node || true)"
if [ -z "$NODE_BIN" ]; then
  NODE_BIN="$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node"
fi
"$NODE_BIN" frontend/node_modules/vitest/vitest.mjs run --root frontend
