# Chetan's career workspace

This folder has two active workflows: `daily-job-search/` and `career-dashboard/`.
Always read `career-dashboard/AGENTS.md` before candidate or resume work. Its
profile and evidence registry are the only current candidate authorities.
`backup/` is preserved history, never an active template or current profile.

## Continue work from this chat

Read `WORKSPACE-STATE.md`, then run:

```sh
career-dashboard/.venv/bin/python career-dashboard/scripts/career.py jobs
career-dashboard/.venv/bin/python career-dashboard/scripts/career.py activity
```

The dashboard and chat must update the same `career-dashboard/data/career.db`
through `scripts/career.py` / `Workspace` or `scripts/workspace.py` / `CareerServices`; never maintain a second status list.
Use exact job IDs. If a user names an ambiguous employer/role, ask which posting.
Record a submission from explicit user confirmation or a verified matching email. Retain actual submission dates when stated; keep email receipt dates separately and never infer an unknown application date.
Never infer applications, rejection, graduation or new claims from elapsed time.
Status and profile-note changes produce persistent activity events. Review notes
into the evidence registry before using them on a resume, preserving source facts.

For a daily search, follow `daily-job-search/DAILY_BRIEF.md`. Save each posting
in the shared database and attach its ID to the dated search run. Application
artifacts live once, under `career-dashboard/output/applications/`; daily run
manifests point there. Keep older delivered URLs in `daily-job-search/history.csv`
for deduplication. Use the historical-pack index to locate archived originals.

After meaningful work, update `WORKSPACE-STATE.md` with what changed, unresolved
items and next actions. Run `./Check Workspace.command` after code changes.
Use disposable workspaces for mutation tests. Keep backup manifests immutable.
Do not submit applications or contact anyone without explicit authorization.
Do not add a second automation. The existing daily schedule uses this shared data.

## Four-tab application (September 2026)

The active client is `career-dashboard/frontend/` (React/TypeScript). FastAPI in
`dashboard/` serves its build and the shared API on loopback port 8000. `services/`
contains daily planning, editable profile knowledge, email evidence and separate
AI worker runs. Do not revive the archived static client.

Optional AI work runs on a selectable runtime. Codex and Claude are both
supported; choose one in Agent control or with `CAREER_AI_RUNTIME`, and read
`career-dashboard/docs/AI-RUNTIMES.md` before changing `services/ai_runtime.py`.
Mailbox review needs Codex's connected Gmail read tools and stays on Codex
whatever is selected. Do not add a mailbox integration for another runtime
without being asked. Saved AI results are keyed per runtime, so switching one
neither reuses nor discards another's result.

Before daily search or profile comparison, read the active knowledge via
`career-dashboard/.venv/bin/python career-dashboard/scripts/workspace.py profile`.
User-edited entries override their imported wording; deleted entries are excluded.
Original config and evidence remain provenance and the resume wording authority.
Do not silently use old canonical wording after Profile changes. Reconcile the
changed evidence, bump the canonical revision and rebuild/review resume artifacts.
Read the current target with `scripts/workspace.py goals`; the default is 30 per
week, Monday–Saturday, with missed work carried forward. Avoid fixed ten-job
batches unless explicitly requested. Email evidence, run history and goals are
also accessible through `scripts/workspace.py summary` and `/api/v2/summary`.

The hiring-manager worker must receive only the job description and public company
research. Never pass candidate profile, notes, files, mail or chat history to it.
Profile comparison runs afterward in a separate process with active knowledge.
