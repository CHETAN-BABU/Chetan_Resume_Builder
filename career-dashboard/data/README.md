# Career records

`career.db` is the authoritative local SQLite store for saved opportunities, notes and application status. Back it up before replacing a workspace.

`pipeline.md`, `application-tracker.md` and `applied-companies.md` are generated projections for agent workflows. Update records through the dashboard or scripts/career.py; do not edit these projections directly. Only recorded application dates establish submissions.

`historical-packs.json` indexes 20 earlier prepared resumes under `../backup/historical/` (paths are relative to the Resume folder). Source hashes remain unchanged; old QA is not current approval. Thirteen historical daily postings have been imported as saved opportunities with no submission date.


`career.db` also contains dated search runs and append-only activity events. `jobs.json`, `activity.json` and `../daily-job-search/YYYY-MM-DD/run.json` are generated views for this chat. Update through Workspace, the CLI or dashboard; use `career.py export` to refresh views. Profile-note history stores both previous and new text. The activity UI shows the latest 200 events; the database and activity.json keep the complete history.
