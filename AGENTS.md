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
through `scripts/career.py` / `Workspace`; never maintain a second status list.
Use exact job IDs. If a user names an ambiguous employer/role, ask which posting.
Only record a submission from the user's confirmation, retaining its actual date.
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
