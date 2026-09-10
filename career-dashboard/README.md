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

Use `--port 8001` if port 8000 is occupied, or `--no-browser` to start without opening a browser. The app needs Python 3.9+, and does not require Node.js, an API key, a cloud account or a hosted site. Tectonic is required for PDF compilation. This Mac uses Swift/PDFKit to inspect and render PDFs; other platforms need pypdf and Poppler (`pdftoppm`).

## What is ready

- Overview of your profile, approved project bank, current opportunities and historical packs.
- Opportunity capture from a full pasted JD, persistent statuses, notes and actual application dates.
- Complete profile and claim explorer, including conditional and held information; editable update notes.
- Draft preparation selecting exactly one registered project, two-page PDF preview and full validation diagnostics.
- Existing job-verification, resume-tailoring, interview and batch workflows, with paths updated for this workspace.
- A compiled, visually reviewed two-page base resume in `output/base/`.

The dashboard's draft preparation uses exact registered project wording and retains the base summary. Complete JD tailoring, employer research, live-posting checks and evidence review through the documented agent workflow. A saved posting is not automatically verified. A generated PDF is not automatically a reviewed release.

## Your daily workflow

1. Open **Opportunities**. Use a career-page starting point or your preferred job-search tool; save a specific posting and its full JD.
2. Open the opportunity. Inspect the role concerns and select a relevant project.
3. Choose **Prepare new draft**, then **Compile preview**. Each preparation creates a new version, preserving previous edits.
4. In the generated folder, complete the evaluation, company research and `evidence-map.yml`; tailor the resume to the JD. Follow [the tailoring workflow](workflows/TAILORING.md).
5. Choose **Run full checks**. Resolve every failure, inspect both rendered pages, then record the visual review using the release command below.
6. Submit the application yourself. Record **Applied** and the actual submission date in the dashboard.

The profile includes client names and your Irish phone exactly as supplied, per your latest instruction. Earlier dates, alternate contact details and unresolved claims are retained in the full profile. See [the remaining questions](context/QUESTIONS-FOR-YOU.md).

## Folder map

```text
context/          registry, readable profile, confirmation queue, original source notes
config/           identity, disclosure, role targets, saved career-page references
templates/        resume-base.tex and batch/evidence-map examples
scripts/          career operations, PDF validation and batch commands
dashboard/        local FastAPI application and browser interface
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
