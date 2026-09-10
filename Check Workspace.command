#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/career-dashboard"
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
.venv/bin/python ../daily-job-search/with_resume_runtime.py .venv/bin/python -m pytest tests -q
.venv/bin/python scripts/validate_workspace.py
.venv/bin/python scripts/check_layout.py
