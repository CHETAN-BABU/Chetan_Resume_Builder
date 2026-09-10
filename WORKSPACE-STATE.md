# Career workspace state

Updated 10 September 2026 after the folder consolidation.

## Current workflow

- The active app is `career-dashboard/`; launch from the root `Start Dashboard.command`.
- `daily-job-search/` and this chat use the same `career-dashboard/data/career.db`.
- 13 previously delivered daily postings are saved for follow-up. No submissions
  have been established; there are 0 recorded application dates.
- 20 historical resume packs remain preserved in `backup/historical/`; their
  source hashes were checked after relocation. They need current review before use.
- Search history for 5, 6 and 8 September is imported. The 10 September run contains
  cleanup notes and no newly discovered jobs; live discovery was not part of cleanup.
- Profile and evidence revision remain `2026-09-09.1`; the approved base PDF,
  source and candidate evidence were preserved unchanged.
- The existing daily schedule remains active at 09:00 Europe/Dublin, in its
  original task (`01a07303-0916-7623-9e9a-563adb669e36`). Its prompt now uses these
  folders and the latest disclosure preference. Do not create a duplicate schedule.
- This chat is the user's manual application/resume update workspace. All chats
  and scheduled runs must use the shared APIs and update this handover file.

## Next work

1. Reverify any older posting before applying or generating a new tailored version.
2. When Chetan confirms a submission, update its exact job ID and actual date.
3. Review supplied new profile facts through `context/UPDATES.md` and the registry;
   preserve unresolved employment, degree, location and permission details.
4. For a new daily search, use `daily-job-search/search.py` and the current brief.

## Recovery and checks

The pre-cleanup archive contains 2,676 hash-verified files. Retired engines,
old builders, environments, caches and superseded reports are in `backup/`.
The active history has local Git tracking and generated JSON/Markdown views.
Run `Check Workspace.command` for regression tests, workspace consistency,
database integrity, historical source hashes and shared-run link checks.
See `career-dashboard/docs/CLEANUP-REPORT.md` for completed verification.
