# Chetan Career Workspace — agent instructions

This active workspace belongs to **Chetan Babu M**. Read `config/profile.yml`, `context/evidence.yml`, `context/QUESTIONS-FOR-YOU.md`, then `context/PROFILE-NOTES.md`. The registry is the external-wording authority. Raw supplied material lives in `context/sources/`; new notes in `context/UPDATES.md` remain pending until reviewed into the registry.

## Identity and current user preference

Professional identity: Data Analyst / BI Analyst / BI Developer. Academic identity: MSc Data Science candidate. Distinguish professional BI delivery from academic ML, clustering, explainability and candidate retrieval projects.

The user explicitly authorised inclusion of all supplied information on 9 September 2026. Include client names and the Irish phone exactly as supplied. Do not reintroduce the earlier anonymity or phone-omission defaults. Both supplied phone numbers and conflicting location information remain visible in the internal profile; the resume uses Ireland and the supplied Irish number until corrected.

This disclosure preference does not establish an MSc award, a different employment end date, unverified metrics, solo ownership or work rights. Keep January 2025 as the employment end date and the MSc in progress until the conflicts are resolved. Stamp 1G was confirmed on 5 September 2026; earlier expiry and future sponsorship remain unconfirmed. Do not infer current immigration law or eligibility from these notes.

## Evidence and scope

- Preserve every source and any material conflict. Never modify the registry merely to make an invented resume claim pass.
- Keep team attribution. Do not claim professional AI/ML/MLOps engineering, Data Scientist employment, unsupported cloud deployment, migration leadership, contract causality or zero-defect outcomes.
- Conditional claims require their recorded conditions. Held/missing claims remain off resumes. Preserve the capstone's limited-discrimination caveat.
- Prioritise Ireland Data Analyst, BI/Power BI Developer, Reporting/Insights Analyst and Analytics Consultant roles. Evaluate Junior/Graduate Data Scientist and entry-level GenAI application roles only when candidate projects satisfy the actual requirements.
- Exclude unsupported senior, software, hardware, DevOps/MLOps and production platform roles. Read full JDs; title matching does not establish eligibility.
- Never submit applications or send outreach without explicit user authorisation. Preparing a resume is not a submission.

## Layout and state

`context/` contains candidate evidence; `config/` policy and targets; `templates/` rendering templates; `scripts/` executable machinery; `workflows/` agent playbooks; `frontend/` the React UI; `dashboard/` the FastAPI API; `services/` the application services; `data/career.db` active opportunities and statuses; `output/` generated artifacts; `docs/` provenance and verification.

`data/historical-packs.json` indexes earlier prepared packs under ../backup/historical/. No applications were inferred from those files. The Markdown trackers in `data/` are read-only projections; the dashboard database is the active status store. Keep user-recorded application dates; never age an application into a rejection or ghosted state automatically.

## Resume and review contract

Every tailored resume uses one saved JD, exactly one registered resume-ready selected project and exactly two A4 pages. Keep 10pt minimum body text, a single column and the required sections from `config/profile.yml`. Each content construct needs registry evidence IDs; company research never creates candidate experience.

Each reviewed application folder contains:

- `job-description.md`
- `evaluation.md`
- `company-research.md`
- `evidence-map.yml`
- `resume.tex` and `resume.pdf`
- `resume-preview/page-01.png` and `resume-preview/page-02.png`
- `qa.json`

The dashboard prepares a deterministic draft by selecting existing project wording. It retains the base summary and marks role eligibility and requirement review pending. Complete the evaluation, sourced employer research and evidence mapping; tailor the summary and relevant evidence without fabrication. Do not advertise draft selection as full AI tailoring.

Run `python3 scripts/validate_resume.py <folder>/resume.tex --compile --output <folder>/resume.pdf --render-dir <folder>/resume-preview --qa-json <folder>/qa.json`. Inspect both rendered pages. Only after inspecting the current output, rerun with `--visual-review pass --visual-reviewer <reviewer>`. A failed or pending review is not release-ready. Source, PDF, registry and preview hashes must remain current.

Job fit, supported requirement coverage and binary artifact QA are distinct; never describe keyword counts as ATS scores or probabilities.

## Batch requests

“Give me 10 companies” means discover and verify up to ten eligible live postings, research and tailor each, compile, render, inspect and deliver isolated artifacts. Continue replacing expired, duplicate or ineligible leads. If the honest market search yields fewer, report the shortage and search coverage. Use `workflows/modes/batch-resumes.md` and the existing batch scripts. Do not create ten invented matches to satisfy a count.

## Development checks

Use a disposable workspace in tests. Run `python3 -m pytest tests -q` and `python3 scripts/validate_workspace.py`. The dashboard binds only to loopback, rejects foreign browser origins and serves output files through a path-constrained route. Keep profile revision and evidence revision aligned; any changed claim needs a revision bump and rebuilt artifacts.


Root AGENTS.md and WORKSPACE-STATE.md define shared chat/daily-search continuity. Use the shared database APIs for statuses, search runs and profile notes; activity events preserve changes. Retired engines and historical provenance reports are not current instructions.

## Active profile and email evidence

`data/career.db` also owns editable knowledge, goals, email evidence and agent runs.
Use `scripts/workspace.py profile` for active knowledge and `goals` for current
carryover before discovery. Profile removals exclude entries from future matching;
original evidence stays preserved. Resume preparation is guarded in Workspace as
well as the API while active edits await canonical evidence reconciliation.
Verified exact Gmail confirmations establish application status. Keep receipt time
separate from an explicitly stated submission date. Reminders, automated assessments,
marketing, ambiguous roles and silence do not establish an interview or submission.
Gmail workers expose only read tools; no sending, drafting or mailbox changes.
The independent hiring worker never receives candidate context.
