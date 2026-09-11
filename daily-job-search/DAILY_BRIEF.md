# Chetan's daily job search

Requested on 5 September 2026. The active Codex task schedule starts work every day at **09:00 Europe/Dublin**, including weekends, and posts the completed batch in the same task. Resume generation and verification take time after the run starts. Automation ID: `chetan-s-daily-10-jobs-and-tailored-r-sum-s`.

## Outcome

Read the current planner with `career-dashboard/.venv/bin/python career-dashboard/scripts/workspace.py goals`. Find up to the remaining daily application target in unique suitable postings (at most ten per discovery pass). The default is 30 applications per week over Monday–Saturday; unfinished work carries forward. Respect completed targets and resume partially finished searches. Preserve the existing resume workflow; prepare drafts only when active profile changes have been reconciled with the evidence registry. Re-read the active editable profile with `scripts/workspace.py profile` on every run; it overrides imported wording for discovery and matching. Original config/evidence remain the resume authority. Optimize for credible applications and interviews; do not promise an offer or an invented ATS score.

## Candidate evidence and targeting

The source workspace is `/Users/chetan/Desktop/Resume/career-dashboard`. Follow its `AGENTS.md`, `config/profile.yml`, `context/evidence.yml`, career/project narratives and `context/PROFILE-NOTES.md`, in their documented order. The LaTeX template is a layout, not independent evidence.

Prioritize Ireland-based Data Analyst, BI Analyst, Business Intelligence Analyst, BI Developer, Power BI Developer and Reporting Analyst roles. Consider Insights/Analytics roles and junior or graduate data science only where academic evidence is accepted. Preferred locations: Dublin, Cork, Limerick and remote within Ireland; broaden throughout Ireland before reporting a shortage. Relevant domains include pharmaceuticals, FMCG, finance, insurance, healthcare, manufacturing and operations.

The current approved position is approximately two years of Data Analyst/BI Developer experience at Infocepts (February 2023 to January 2025, including the initial training role), plus an MSc programme in Data Science in progress at Munster Technological University (September 2025 to September 2026). Do not infer completion from the calendar. Distinguish professional, training, academic and candidate-project evidence.

Use only supported claims and registered projects. Preserve team attribution. Include client names and the Irish phone exactly as supplied, following the 9 September disclosure instruction in the canonical profile. Omit visa claims from resumes by default. On 5 September 2026 Chetan confirmed **Stamp 1G**; use the new registry entry `WORKAUTH-STAMP-001` when assessing roles or answering a required permission question. Future sponsorship and current expiry remain unconfirmed. Never infer duration, renewal or permanent work rights. Record explicit employer eligibility requirements as gaps or blockers when the supplied facts do not establish them.

## Discovery and delivery

1. Read prior daily folders and `history.csv`, the older dated batches, `career-dashboard/data/jobs.json`, `career-dashboard/data/application-tracker.md` and `career-dashboard/data/historical-packs.json`. Exclude already-applied and previously delivered exact postings. A new suitable role at a previously listed employer may qualify on another day. Deduplicate by canonical URL/requisition ID, not just URL spelling.
2. Search the live web and open specific postings. Verify employer, title, Ireland location, description, seniority, deadline if available and an active application route. Prefer employer or authorized ATS sources. Search snippets, old PDFs and generic careers pages alone are insufficient. Record access date and uncertainty honestly.
3. Evaluate mandatory requirements before ranking. Reject clear experience, role or location mismatches. Do not pad the target with senior roles or unsupported production engineering. Explain manageable gaps separately from strengths.
4. Keep replacing rejected, closed, inaccessible and duplicate leads across approved roles and Irish locations. If enough honest matches are unavailable after a broad search, release every valid match and document the exact shortage, search coverage and rejected leads.
5. For each selected JD, save a concise sourced snapshot, company-problem research and requirement-to-evidence map. Write a distinct summary, skill ordering and experience emphasis, and select exactly one relevant resume-ready registered project. Do not imply the project was built for the target company.
6. Generate a selectable-text, single-column, exactly two-page A4 PDF plus editable LaTeX source using the existing template. Run `scripts/validate_resume.py` with compile, output, render and QA arguments. Visually inspect both pages. Resolve layout and factual issues before release; then run a cross-batch audit for consistency, duplicate jobs and near-identical tailoring.
7. Create a run with `career-dashboard/.venv/bin/python daily-job-search/search.py start`. Save each full posting with `search.py add --file POSTING.json` (company, title, location, url, description); this updates the same database as the dashboard. Prepare through `career-dashboard/scripts/career.py prepare JOB_ID`. Keep one versioned company/job folder under `career-dashboard/output/applications/`; the dated `daily-job-search/YYYY-MM-DD/run.json` points to it. Save daily batch summaries and search coverage under the dated search folder. Required files: `job-description.md`, `evaluation.md`, `company-research.md`, `evidence-map.yml`, `resume.tex`, `resume.pdf`, `resume-preview/page-01.png`, `resume-preview/page-02.png`, `qa.json`. Save `batch.yml`, `batch-qa.json`, `companies.md` and search coverage at the date level. Resume a partially completed same-day run instead of overwriting or duplicating it.
8. Deliver a ranked table with company, role, location, direct application link, supported fit, key gap and links to the resume PDF and job folder. Highlight the best three next applications (or all if fewer than three). Explain shortages or failed artifacts explicitly.
9. Update `history.csv` with date, company, role, canonical URL, requisition ID when known, location, state and artifact path. States describe facts: discovered, rejected, prepared, delivered or user-confirmed applied. Never mark an application submitted merely because its resume exists.

## Local PDF runtime

The existing Tectonic compiler needs a local cached bundle in this sandbox, and Swift/PDFKit needs writable module caches. Prefix validator commands with `python3 /Users/chetan/Desktop/Resume/daily-job-search/with_resume_runtime.py`. This reuses the installed compiler and existing cached LaTeX files, creates caches within this workspace, and leaves the validators unchanged. For example:

```sh
python3 daily-job-search/with_resume_runtime.py /usr/bin/python3 career-dashboard/scripts/validate_resume.py PATH/resume.tex --compile --output PATH/resume.pdf --render-dir PATH/resume-preview --qa-json PATH/qa.json --evidence-map PATH/evidence-map.yml
```

Visual inspection is still required. Only after viewing both pages may a follow-up validation record `--visual-review pass --visual-reviewer "Codex visual inspection"`. Run `validate_batch.py` through the same runtime wrapper. The retired `build_daily.py` is archived. Use `search.py` and the current dashboard `scripts/career.py` to prepare drafts, then complete genuine JD tailoring and research through the workflow. No code from backup is an active dependency.

## User interaction

The user requested a daily result. Report each completed batch and actionable failures here; avoid repeated unchanged progress notifications. Research and local document preparation are authorized. Do not submit applications, contact recruiters or upload candidate files to external portals without explicit authorization.

Keep the computer powered on, the desktop app running and this folder available for local scheduled work. See [official scheduled-task guidance](https://learn.chatgpt.com/docs/automations?surface=app).

## Candidate confirmations to collect when convenient

- Current preferred phone number and international formatting.
- Current expiry date and any future sponsorship need; Stamp 1G is already confirmed.
- Whether the MSc has been awarded and its exact title; retain in-progress until confirmed.
- Whether January 2025 or July 2025 is the correct employment end date; retain the canonical January date meanwhile.
- Public credential/project links. Client disclosure is already authorized.

These pending details do not prevent evidence-safe research or resume preparation.

## Shared tracking and continuity

`career-dashboard/data/career.db` owns application statuses and dated search runs. `run.json`, `data/jobs.json`, `data/activity.json` and Markdown trackers are generated views. Never edit those views as a substitute for a database update. Use `search.py notes --file NOTES.md` for coverage, rejected leads and shortages. Update `WORKSPACE-STATE.md` after delivery. The older 20 packs live in `backup/historical/`; `history.csv` retains their delivered URL history, not proof of submissions. The scheduled task continues in its original task while this chat can maintain the same files.

## Email and independent reviews

Use the dashboard Gmail sync or `scripts/workspace.py run --kind email` to review
job-related mail through the connected read-only Gmail tools. Exact unique matches
can update automatically; unmatched or ambiguous messages stay pending. Reminders
never count as applications. Confirmed receipt dates are distinct from actual dates.
For an in-depth saved-role review, use `scripts/workspace.py run --kind research
--job-id JOB_ID`. It runs public company research, an independent hiring benchmark
without candidate context, then a separate active-profile comparison. All results
are stored in the dashboard; original research limitations must remain visible.
