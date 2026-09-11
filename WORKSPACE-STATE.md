# Career workspace state

Updated 11 September 2026 after the four-tab React upgrade.

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
actual dates only when supplied. Resume Studio’s further customization awaits
Chetan’s promised brief. Canonical revision remains 2026-09-09.1; preserve the
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
