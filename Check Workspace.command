#!/bin/bash
# Backend tests, workspace validation, the production client build and client tests.
set -euo pipefail
cd "$(dirname "$0")/career-dashboard"
export PATH="/opt/homebrew/bin:/usr/local/bin:$HOME/Library/pnpm:$PATH"
.venv/bin/python ../daily-job-search/with_resume_runtime.py .venv/bin/python -m pytest tests -q
.venv/bin/python scripts/validate_workspace.py
.venv/bin/python scripts/check_layout.py

.venv/bin/python scripts/build_frontend.py
NODE_BIN="$(.venv/bin/python -c 'import sys; sys.path.insert(0, "scripts"); from build_frontend import node_binary; print(node_binary() or "")')"
if [ -z "$NODE_BIN" ]; then
  echo "Node.js was not found, so the client tests could not run. Install Node.js or set CAREER_NODE_BIN." >&2
  exit 1
fi
"$NODE_BIN" frontend/node_modules/vitest/vitest.mjs run --root frontend
