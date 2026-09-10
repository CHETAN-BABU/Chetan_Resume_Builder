# Cleanup and verification — 10 September 2026

The Resume folder now has two active workflows: daily-job-search and
career-dashboard. The newer personal dashboard is the only current profile,
resume and application engine. Root launchers, README, AGENTS.md and
WORKSPACE-STATE.md provide one entry point and persistent AI handover.

## Preserved and moved

The original active folders were archived before relocation, with all 2,676
regular files verified against SHA-256 hashes. See
`../../backup/2026-09-10-before-cleanup/verification.json`.

- `example/` became `career-dashboard/`.
- The older resume engine, dependent daily builder, unused environments and
  superseded rebuild reports moved to `backup/retired/`.
- Existing backups moved to `backup/previous-backups/`.
- All old dated packs and the Arup pack moved to `backup/historical/`.
- All 20 indexed historical resume source hashes still match.
- Candidate profile, evidence, base template and base PDF content were unchanged.
- Historical internal links in preserved documents describe their original paths;
  the active historical index and delivery CSV point to the relocated files.

## Shared tracking

Thirteen previously delivered daily postings were imported as saved opportunities
with the original JD snapshots and archive references. None was marked applied.
Three historical search runs were imported, and today's empty run records the
cleanup. Application status, dates, notes, draft versions and daily-run membership
share one SQLite database. JSON and Markdown projections support chat continuity.

Persistent activity records preserve job/status/draft changes, search notes and
before/after profile-note text. Status updates now retain existing notes and
submission dates when those fields are omitted. Profile-note changes remain
pending until reviewed into the canonical evidence registry.

The daily schedule was updated in place, preserving its name, cadence, active
state and original task. It now reads the current profile, uses the shared
application database and writes resumes into versioned dashboard output folders.

## Verification

- Regression suite: 47 tests passed, including PDF compilation, batch release
  checks, stale artifact detection, application/date persistence, event history,
  database migration, daily-run idempotence, API behavior and path/origin rejection.
- Workspace validation: PASS.
- Layout/database/projection/historical-hash checks: PASS.
- Dependency consistency: `pip check` passed.
- Root launcher started the relocated app; a second launch detected and reused it.
- Browser checks: overview counts, daily screen, run creation, notes save and
  reload persistence, activity history and current base-resume availability.
  No browser JavaScript errors were recorded after the final reload.

Tests that mutate records use disposable workspaces. No fabricated application
was added to the user's database. Today's browser save contains real cleanup
notes. Historical jobs were not reverified by this cleanup, and no applications
were submitted. Complete JD tailoring and visual QA remain required for new
resume releases.
