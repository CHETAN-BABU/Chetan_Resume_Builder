# Daily job search

Follow `DAILY_BRIEF.md` for discovery, eligibility, evidence and release checks.
From the Resume folder:

```sh
career-dashboard/.venv/bin/python daily-job-search/search.py start
career-dashboard/.venv/bin/python daily-job-search/search.py add --file POSTING.json
career-dashboard/.venv/bin/python daily-job-search/search.py list
```

Posting JSON fields: company, title, location, url, description (full JD).
`search.py link JOB_ID` attaches an existing opportunity to today; add `--date
YYYY-MM-DD` for another run. `search.py notes --file NOTES.md` saves search coverage.
The dashboard offers the same daily controls. Resumes live in the dashboard's
versioned output folders. Dated run.json files are generated database views.

`history.csv` retains previously delivered postings for deduplication. Old PDFs
and batches are preserved under `../backup/historical/`; no file was deleted.
