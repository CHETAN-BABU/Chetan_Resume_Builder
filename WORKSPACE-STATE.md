# Career workspace state

Updated 12 September 2026 after implementing Resume Studio.

## Current application

- One local React/TypeScript client with exactly Dashboard, Daily Search, Resume
  Studio and Profile. FastAPI serves the build and API on 127.0.0.1:8000.
- Root Start Dashboard.command builds changed frontend sources automatically.
  Resume.code-workspace opens the cleaned root in VS Code.
- Mutable jobs, profile entries, goals, email evidence and worker history live in
  career-dashboard/data/career.db. Chat commands in scripts/workspace.py and
  scripts/career.py use the same database. JSON/Markdown files are projections.
- 14 saved postings: the previous 13 are preserved, including the user-prepared
  FedEx draft. Arup IRE0000HN was added from its preserved full JD and linked to
  the actual Gmail confirmation. Status is applied; actual submission date is
  unknown. Confirmation arrived 8 September 23:39 UTC / 9 September Dublin.
- Gmail is connected as chetanbabu07@gmail.com. A live read-only sync reviewed
  35 messages; 1 is confirmed and 34 remain pending/unlinked/ambiguous. No human
  interview or offer was verified. The coverage statement is visible in the app.
  Reminders and automated assessments do not establish applications/interviews.
- Goals default to 30 applications per full week over Monday–Saturday, starting
  11 September. This first partial week has a target of 10; today’s base target
  is 5. Missed work carries across days/weeks; duplicates never earn extra credit.
- Profile has 83 active imported entries, including editable target-role/location
  preferences. Six agent/workflow descriptions and original evidence are visible.
  Edits affect discovery/comparison; resume preparation waits for canonical
  evidence reconciliation after edits. No new candidate claims were invented.
- Arup’s live public company research, independent hiring benchmark and separate
  profile comparison completed and are visible in its job record. The hiring
  worker has no profile, email, workspace files or conversation context.
- An initial discovery pass timed out. Discovery now has a bounded query/page
  budget and returns up to three verified jobs per pass. The successful retry
  returned zero new verified matches with explicit coverage and rejected leads;
  it did not repeat old jobs or invent results. Saved jobs and high-confidence
  email application evidence both feed deduplication, including unlinked roles.

## Existing schedule and continuation

The original daily automation remains active at 09:00 Europe/Dublin in task
01a07303-0916-7623-9e9a-563adb669e36. Its name is now “Chetan’s daily career plan”.
Its prompt reads the active profile, current carryover and shared database.
No duplicate automation was created. Optional in-app periodic Gmail sync is off
by default; enable it in Dashboard settings to run while the server is running.

Read current state with:

    career-dashboard/.venv/bin/python career-dashboard/scripts/workspace.py summary
    career-dashboard/.venv/bin/python career-dashboard/scripts/workspace.py profile
    career-dashboard/.venv/bin/python career-dashboard/scripts/workspace.py goals

Continue reviewing unmatched email evidence against exact saved postings. Record
actual dates only when supplied. Resume Studio is now implemented as described below. Canonical revision remains 2026-09-09.1; preserve the
MSc in-progress status, January 2025 employment end date and evidence caveats.

## Verification and recovery

- 73 Python tests and 5 frontend tests pass (78 total); TypeScript/production
  build, profile validator, database integrity, historical hashes and shared
  search projections pass. Browser CRUD, carryover, four-tab navigation, completed
  research rendering and a 390px layout were exercised. No browser console errors.
- 20 historical resume packs and both current PDFs remain preserved. No new
  resume release or visual approval was claimed during this application upgrade.
- backup/2026-09-11-before-react-upgrade/ holds the pre-upgrade database/source
  archive and the retired static UI with a verified four-file SHA-256 manifest.
- backup/2026-09-11-after-four-tab-upgrade/ holds the upgraded database snapshot
  and retired IDE shortcut. If VS Code recreates its old compatibility folder,
  it contains only a workspace shortcut; no retired application engine runs there.
- Codex/Gmail/web availability can still vary. Failed runs remain in history,
  partial completed research is retained, and retry controls do not infer results.


## Resume Studio — 12 September 2026

- Dashboard and Daily Search job clicks open a persistent Studio draft keyed by
  exact job ID. Easy edit and full LaTeX source sit beside revision-specific PDF
  page previews. Copy/download source, auto-save, explicit save/compile and
  restore-as-new-version controls are implemented.
- First-open drafts use the current registered template/project evidence with
  JD-based project selection and skill ordering. Existing prepared packs retain
  their wording. These are editable starting drafts, not completed AI tailoring.
- Agent 1 uses separate isolated company-research and resume-advice processes;
  neither receives candidate profile, notes, email or chat history. Runs start
  automatically on first open and expose retry/refresh and dated sources.
- Agent 2 records new user-added projects and skills in the shared Profile table,
  deduplicates repeated content, keeps versions and flags missing projects.
  Add my own project replaces the complete selected project without inheriting
  old bullets. Captures remain user-supplied pending evidence review.
- Canonical profile/evidence revision is still 2026-09-09.1. Reconcile new Profile
  facts before release or creating further new drafts. Existing Studio drafts
  remain editable and visibly marked as drafts. No resume release, application,
  candidate claim, email or new automation was inferred by implementation tests.
- Original application packs remain preserved; Studio projections live within
  their application folders under studio/. SQLite owns drafts, history and
  captures. Full behavior and limitations: career-dashboard/docs/RESUME-STUDIO.md.
- Verification: 81 Python tests and 7 frontend tests (88 total), production build,
  profile/workspace validators, database relationships and historical hashes.
  Disposable browser checks confirmed job routing, auto-save, project/skill
  capture, real two-page preview and mobile layout. UI agent reports were fixtures;
  live research runs on the user's first opening of each actual job.

The updated dashboard was restarted successfully on 127.0.0.1:8000 and Resume
Studio was opened for the user. Its new API routes are present; disposable UI
checks ran separately on port 8001 and that test server has been stopped.


## Daily career run - 12 September 2026, morning

- Resumed the shared dated run. No pending profile edits; canonical revision 2026-09-09.1 unchanged. Now 16 saved postings.
- Added KPMG 2826 as job `1acf78884105297f` and Accenture FY28 as job `fff05ec16dd35b33`. Full primary JDs and active application routes verified in browser.
- KPMG public research, independent hiring benchmark and separate active-profile comparison persisted as research run `ed1d1050ed1d4ac1b354cf6a24560ad9`, using completed collaboration-worker results. Hiring inputs contained only the JD and public research.
- One tailored two-page draft at `career-dashboard/output/applications/1acf78884105297f-i4s8l2l7/`. Both pages inspected; actual PDF renderings matched viewed previews. QA fails only for unresolved mandatory overall predicted 2:1/equivalence. `role_eligible` remains false; draft not released. Question pending with user.
- Accenture form warns AI-assisted applications may be withdrawn. Saved as manual candidate-writing option; no AI résumé. Future availability, degree equivalence and permission unconfirmed.
- Email worker failed immediately. Read-only Gmail fallback succeeded; three job-related bodies were invitations/newsletter, with no new status. The 34 older pending matches remain unchanged; Arup's actual submission date is unknown. Coverage stored in shared Gmail preferences and search notes.
- Fifteen queries covered Ireland, Dublin, Cork, Limerick, Galway and remote roles. Exclusions in `daily-job-search/2026-09-12/search-coverage.md`. Eight-role discovery shortfall, zero approved releases, no applications submitted. Batch QA also fails while KPMG remains pending; Accenture was excluded from the AI résumé batch, not rejected by the employer.
- Planner stays 0/10 today: five base plus five carryover. Existing 09:00 schedule unchanged. History CSV adds prepared/discovered entries.
- Next: confirm KPMG overall predicted 2:1/equivalence, availability and permission before release/application; candidate writes Accenture materials; continue BI/reporting discovery and exact email matching. No code changed during this daily run; pre-existing Resume Studio changes preserved.


## Resume page-fill upgrade — 12 September 2026

- Added a ranked Fill two pages operation and first-preview fitting. Supported
  detail expands only from active registered evidence; original custom summary
  wording, dates, ownership and caveats remain intact. No new profile claim or
  canonical revision is introduced by formatting existing evidence.
- Layout acceptance now measures both page usage and gaps in actual rendered
  pages, in addition to requiring two A4 pages and readable 10–12pt body text.
  Successful fits are saved as new versions; failures preserve the prior draft.
- Current request concerns Accenture job fff05ec16dd35b33 and its Studio draft.
  The saved employer note about candidate-written applications remains relevant;
  a layout fit does not establish release readiness or application eligibility.
- Completed Accenture Studio revision 2 at
  `career-dashboard/output/applications/fff05ec16dd35b33-wijtws6k/studio/preview-2/`.
  PDF is exactly two A4 pages, with 95.8% and 96.0% content-height usage,
  10.94pt body text and no overfull boxes. Both latest rendered pages were
  visually inspected: no clipping, split bullets or large blank bands. The
  original prepared pack and Studio version 1 remain preserved.
- Added opt-in `--studio-layout` validation for the supported density block,
  ranked section order and actual page-fill measurements. Default legacy
  validation remains intact. Each preview stores its own source, JD snapshot
  and matching evidence references; generated details do not create Profile
  duplicates. Registry/profile revision remains 2026-09-09.1 with no pending edits.
- Final artifact QA now fails only for the existing unresolved role eligibility
  and empty requirement review. It is explicitly a draft, not a released
  application. Employer AI-use note, availability/equivalence/work-permission
  questions and application status were not overridden by the layout change.
- Final verification: 85 Python tests and 7 frontend tests (92 total), production
  build, profile/workspace integrity and all 20 historical-pack hashes pass.
  Production dashboard was restarted; browser confirmed saved version 2,
  Fill two pages, both previews and the 95.8%/96% measurements.
- Next: use Fill two pages after substantial source changes; retain evidence
  reconciliation and role-specific review before release. No new automation,
  application submission or outreach was performed.
