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

Optional AI work (public research, discovery, free-text interpretation and
document review) runs on a selectable runtime: **Codex** or **Claude**. Choose one
in Agent control, inside Resume Studio. Everything else — instructions, project
ranking, page fitting, compilation and the term-coverage score — is deterministic
Python and needs no model. Mailbox review needs Codex's connected Gmail tools and
stays on Codex. See `career-dashboard/docs/AI-RUNTIMES.md`.

`career-dashboard/` contains the React frontend, Python API/services, evidence,
SQLite state and versioned resume artifacts. `daily-job-search/` contains the
existing schedule’s brief, history and dated run projections. `backup/` preserves
retired code, original sources, historical packs and recovery snapshots.

Run **Check Workspace.command** for backend/frontend tests, the production build
and integrity checks. Read **WORKSPACE-STATE.md** for current handover notes and
**career-dashboard/README.md** for architecture and commands. Local Git tracks
source and readable state; the database and artifacts have separate backups.
