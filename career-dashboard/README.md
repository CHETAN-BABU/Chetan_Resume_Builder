Current system: [Agent architecture and end-to-end workflow](docs/AGENT-ARCHITECTURE.md).

# Chetan's Career Workspace

Your Ireland job-search and resume workspace, rebuilt around your BI experience and academic data science evidence. Start with the local dashboard, or use the same files through the agent workflows and command line.

## Start the dashboard

On this Mac, double-click **Start Dashboard.command**. It creates an isolated Python environment on first use if needed, then opens http://127.0.0.1:8000. Stop the server with Ctrl+C in its Terminal window.

For manual setup, from this folder:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python dashboard/run.py
```

Use `--port 8001` if port 8000 is occupied, or `--no-browser` to start without opening a browser. The app needs Python 3.9+, and uses Node.js + pnpm to build the React client. The launcher detects the bundled Codex runtime on this Mac. Codex sign-in is required for research/discovery; connected Gmail is required for email sync. No separate API key or hosted site is needed. Tectonic is required for PDF compilation. This Mac uses Swift/PDFKit to inspect and render PDFs; other platforms need pypdf and Poppler (`pdftoppm`).

## Four tabs

- **Dashboard**: saved jobs, status/notes/date editing, linked Gmail evidence and activity. Sync Gmail reads job-related mail; exact unique saved company/role matches can update automatically, while ambiguous messages wait for review. Receipt dates and explicitly stated submission dates remain distinct.
- **Daily Search**: editable weekly targets, chosen workdays, partial-week prorating, missed-target carryover across weeks, bounded live job discovery (up to three new jobs per pass) and persistent deduplication by posting/requisition. The default is 30 applications per week over Monday–Saturday.
- **Resume Studio**: preserved PDF library and existing per-job draft, compile and validation tools. Further customization awaits your brief. Edited profile facts pause new drafts until the canonical registry is reconciled, so old facts cannot silently reappear.
- **Profile**: editable personal details, skills, experience, education, certifications, projects and facts; original sources; agent inputs and workflow inventory. Removal is soft and preserves its audit history.

Open a saved job to run company research, an independent hiring-manager benchmark,
and a separate active-profile comparison. Each is a fresh Codex process. The hiring
worker receives only the JD and public research, with no candidate profile, notes,
mail or prior conversation. Sources, limits, stages and previous reports are saved.
Gmail exposes only explicitly allowed read tools; no mail is sent or modified.
Workers require Codex access and may fail when upstream services or usage are unavailable.
Errors remain visible and can be retried; partial research is retained.

## Daily workflow

1. Open **Daily Search**, review today's remaining target and run **Find suitable jobs**.
2. Open a saved posting. Review its full JD, run **Company & hiring review**, and examine the separate profile comparison.
3. Use **Resume tools** for the existing registered-project draft workflow. Finish genuine tailoring, evidence mapping and visual review before release.
4. Apply yourself, then record the actual application date or sync Gmail for confirmation.
5. Review unmatched email evidence and your carried-forward target. Update **Profile** whenever your evidence changes.

The app serves one built React client and one API on `http://127.0.0.1:8000`.
The existing 09:00 Dublin schedule uses the same files and planner. Optional periodic
Gmail sync runs only while the dashboard server is running; configure it in Dashboard.
For development, run `pnpm dev` inside `frontend/` alongside the local API server.

The profile includes client names and your Irish phone exactly as supplied, per your latest instruction. Earlier dates, alternate contact details and unresolved claims are retained in the full profile. See [the remaining questions](context/QUESTIONS-FOR-YOU.md).

## Folder map

```text
context/          registry, readable profile, confirmation queue, original source notes
config/           identity, disclosure, role targets, saved career-page references
templates/        resume-base.tex and batch/evidence-map examples
scripts/          career operations, PDF validation and batch commands
frontend/         React + TypeScript screens and component tests
dashboard/        FastAPI routes serving the same local app
services/         goals, profile, posting identity, Gmail evidence and Codex workers
workflows/        discovery, tailoring, review and interview guidance
data/             career.db, tracking projections and historical-pack index
output/           base PDF and isolated application versions
interview-prep/    Chetan's interview story bank
tests/            inherited and new regression tests
docs/             rebuild plan, provenance, migration and verification report
.agents/          URL-verification skill adapter
.github/          agent adapters pointing to Chetan's policy
```

## Build and release commands

Build the base resume:

```bash
.venv/bin/python scripts/validate_resume.py templates/resume-base.tex --compile --output output/base/Chetan_Babu_M_Resume.pdf --render-dir output/base/resume-preview --qa-json output/base/qa.json
```

For a tailored application, use the same command with its own `resume.tex`, PDF, preview and QA paths. After inspecting both current preview images, add `--visual-review pass --visual-reviewer "Your name"`. Never record a pass without inspecting the rendered output.

Other commands:

```bash
.venv/bin/python scripts/career.py status
.venv/bin/python scripts/career.py jobs
.venv/bin/python scripts/career.py projects
.venv/bin/python scripts/career.py prepare JOB_ID --project PROJ-AZ-RECON
.venv/bin/python scripts/career.py preview JOB_ID
.venv/bin/python scripts/career.py validate JOB_ID
.venv/bin/python scripts/validate_workspace.py
.venv/bin/python -m pytest tests -q
.venv/bin/python .agents/skills/verify-job-url/scripts/verify_job_url.py --url 'https://careers.company.com/specific-posting'
```

URL-verifier results are signals; authentication walls and JavaScript pages can require browser review. Verify current job details before applying.

## Backups and existing work

The full pre-cleanup snapshot is in `../backup/2026-09-10-before-cleanup/`. Older reference backups are in `../backup/previous-backups/`. Twenty earlier packs are indexed in `data/historical-packs.json` under `../backup/historical/`; previous QA is not a current release approval. Thirteen previously delivered daily postings are saved for follow-up, with no application status inferred. See the root README and WORKSPACE-STATE.md for the unified workflow.

See [cleanup and verification](docs/CLEANUP-REPORT.md) and [the source map](docs/SOURCES.md). Earlier rebuild reports are preserved in `../backup/retired/rebuild-docs/`.


The **Daily search** screen and `../daily-job-search/search.py` use this same database. **Activity** keeps job, status, draft, profile-note and search-run changes. `scripts/career.py activity` reads that history; `scripts/career.py notes --file NOTES.md` saves reviewed-input notes from this chat. `scripts/career.py export` refreshes all text projections.

## Chat continuity and checks

Use `scripts/workspace.py summary`, `goals`, `profile`, `mail`, or `runs` to inspect
the same live SQLite data shown in the app. `save-profile --file ENTRY.json --id ID`
uses optimistic revisions; omit the ID to add an entry. `remove-profile --id ID`
preserves audit history. `confirm-mail --id MESSAGE_ID --job-id JOB_ID` links
verified evidence. `run --kind research --job-id JOB_ID`, `run --kind email` and
`run --kind discovery` invoke the same workers as the UI. `export` refreshes the
readable projections. Never edit generated JSON/Markdown instead of SQLite.

From the root, `Check Workspace.command` runs backend regression tests, profile
and layout integrity checks, the React production build and component tests.
Frontend dependencies are locked in `frontend/pnpm-lock.yaml`; the approved
esbuild build script is listed in `frontend/pnpm-workspace.yaml`.

Agent isolation and tool settings follow the [official Codex configuration
reference](https://developers.openai.com/codex/config-reference/). Gmail's connector
is disabled by default except for the explicit read-tool allowlist; unrelated apps,
mail mutation tools, filesystem shell tools and hiring-stage web search are disabled.
The first unbounded live discovery attempt timed out; bounded passes now cap queries
and return verified findings or honest shortages. Upstream availability still varies.
