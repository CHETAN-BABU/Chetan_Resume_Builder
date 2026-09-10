# Chetan's job search and career dashboard

Double-click **Start Dashboard.command** to open your personal dashboard.

You have two working areas:

| Folder | Purpose |
|---|---|
| `daily-job-search/` | Daily search brief, dated run summaries and previously delivered URLs |
| `career-dashboard/` | Personal dashboard, application database, profile evidence and resume versions |
| `backup/` | Original snapshot, retired code and historical resume packs |

Use **Daily search** to organize the day's opportunities. Use **Opportunities**
to record actual application dates, interviews, offers and notes. Use **Resume
studio** to prepare and inspect resume versions, and **Your profile** to record
new information for review. **Activity** retains changes for you and this chat.

Tell this chat things like “I applied to [company and role] on 10 September”,
“Update my project with this result”, or “Find today's matching jobs”. The AI
reads and updates the same local records used by the dashboard. Resume drafts
still need evidence review and both-page visual checks before release.

`WORKSPACE-STATE.md` records current handover notes. `AGENTS.md` tells future AI
sessions how to maintain the workspace. No application is inferred from a PDF.

Run **Check Workspace.command** to run the regression suite and integrity checks.
See `career-dashboard/README.md` for manual commands and resume validation.
For recovery, see `backup/README.md`. Local Git tracks source and text records;
the database, generated files and runtime are protected separately by backups.
