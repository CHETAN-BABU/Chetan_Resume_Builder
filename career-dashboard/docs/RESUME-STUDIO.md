# Resume Studio

Implemented 12 September 2026.

Click a job in Dashboard or Daily Search to open `#resumes/<exact-job-id>`.
The first opening copies the current template (or preserves the existing prepared
pack's wording), selects a registered project by JD overlap and orders existing
skills against the JD. This is a deterministic starting draft, not a completed AI
tailoring or eligibility review.

## Editing

- Easy edit covers summary, core skills and the selected project.
- LaTeX source edits every section and layout. Copy template or download the
  current source to use it in Overleaf.
- Add my own project replaces the selected project with a complete set of new
  details; it does not inherit the previous project's bullets.
- Auto-save and preview run after a short pause. Save & preview also works
  manually. Unsaved edits are retained in the browser session across tab changes.
- Each changed save creates a database version. Restore creates another version;
  old versions and captured Profile entries remain available.
- A failed compile keeps the saved source and previous successful preview. The UI
  explicitly marks outdated previews. PDFs are draft previews, never reviewed
  releases. More/fewer than two pages are shown with an adjustment reminder.

## Agents

Agent 1 automatically starts a durable `resume_advisor` run the first time a job
opens. Company research and advice use two isolated processes receiving only
allow-listed job fields and public research. No profile, resume, notes, email,
workspace files or chat history is passed. The advisor suggests resume priorities,
skills and proposed projects; ideas never become candidate claims automatically.
Refresh research retries failures or requests newer research.

Agent 2 is deterministic. Saves compare selected-project macros, CoreSkills and
Technical Skills in the supplied template. New user-entered project/skill facts
are captured in the shared Profile knowledge table with source job ID and
`user_updated` review state. Exact repeats are deduplicated. Same-title project
edits update a previously captured entry with an audit event. Restoring a version
does not create new Profile facts. Arbitrarily renamed sections/macros in custom
LaTeX are outside this parser; keep the template fields for automatic capture.

Original config/evidence files are unchanged. Captured facts require canonical
reconciliation and a revision bump before resume release. Existing Studio drafts
remain editable while Profile is dirty; creating new drafts still respects the
workspace's evidence-reconciliation guard.

## Storage and verification

`studio_drafts`, `studio_versions`, `studio_captures`, knowledge and activity all
live in the existing `data/career.db`. Artifacts are projections under the job's
application folder, in `studio/`; successful previews use revision-specific
subfolders. The original prepared pack remains available in Job details, clearly
labelled separately from Studio edits. No new status list or automation exists.

The Studio API applies the existing loopback/origin guards. Saves use optimistic
revision checks, atomic SQLite transactions and a process lock for initialization
and compilation. Compilation runs Tectonic in untrusted mode in a temporary
folder with a timeout. A preview is current only if its source hash matches the
saved draft; it still requires evidence, layout and visual review for release.

Verification: Python tests cover persistence, profile capture/deduplication,
version restore, stale writes, deleted projects, dirty-profile guards, advisor
isolation, API origin protection and real two-page compilation. Frontend tests
cover nested LaTeX fields and safe punctuation. Disposable browser checks exercise
Dashboard and Daily Search navigation, automatic skill/project capture, preview
updates and a 390-pixel layout. Agent responses in UI tests are explicit fixtures;
they do not represent a new live company-research result.
