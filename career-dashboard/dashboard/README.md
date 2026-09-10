# Local dashboard

Start from the workspace root with `.venv/bin/python dashboard/run.py`, or double-click `Start Dashboard.command`.

FastAPI serves a plain HTML/CSS/JavaScript interface. No Node build, hosted service, LLM provider, hidden scan scheduler or external messaging integration is needed. The service binds to 127.0.0.1, rejects cross-origin requests and serves artifacts only from output/.

The database is data/career.db. Profile and projects come directly from config/profile.yml and context/evidence.yml. Profile update notes are stored in context/UPDATES.md pending incorporation; they never silently authorise claims. Per-job build locks prevent overlapping requests from mixing artifacts. Each preparation creates a new folder, preserving earlier edits.

Screens: Overview, Opportunities, Resume studio, Evidence & projects, Your profile. Saved-posting details provide project selection, draft preparation, preview compilation, validation diagnostics, status changes and notes.

The inherited reference dashboard's automated AI scanning/chat features were not carried into this implementation. Discovery, employer research and complete resume rewriting run through the existing documented agent workflows. The UI labels this distinction explicitly.
