# Chetan’s career workspace

Double-click **Start Dashboard.command** to open the single local application at
http://127.0.0.1:8000. Use **Resume.code-workspace** to open this root in VS Code.

The application has exactly four tabs:

| Tab | What it does |
|---|---|
| Dashboard | Application progress, linked Gmail evidence, activity and company/hiring reviews |
| Daily Search | Unique saved postings, dated history, weekly target and missed-work carryover |
| Resume Studio | Existing resume library, registered-project drafts, preview and validation |
| Profile | Editable knowledge, original sources, agent inputs and workflow inventory |

Tell this chat “I applied to [company and role] on [date]”, “Update my project”,
or “Find suitable jobs”. The chat, dashboard and daily schedule use the same
SQLite database. Email confirmations keep receipt time separate from actual
submission dates. Preparing a resume never counts as applying.

`career-dashboard/` contains the React frontend, Python API/services, evidence,
SQLite state and versioned resume artifacts. `daily-job-search/` contains the
existing schedule’s brief, history and dated run projections. `backup/` preserves
retired code, original sources, historical packs and recovery snapshots.

Run **Check Workspace.command** for backend/frontend tests, the production build
and integrity checks. Read **WORKSPACE-STATE.md** for current handover notes and
**career-dashboard/README.md** for architecture and commands. Local Git tracks
source and readable state; the database and artifacts have separate backups.
