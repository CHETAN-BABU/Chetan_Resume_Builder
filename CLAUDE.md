# Chetan's career workspace

Read [AGENTS.md](AGENTS.md). It is the single policy source for this workspace and
applies identically to every assistant. Nothing below replaces it.

## Claude-specific notes

The application runs the same way on any machine: double-click
**Start Dashboard.command** (or run it from a shell) and open
http://127.0.0.1:8000. It needs Python 3 and Node.js; the client falls back to
the build already on disk when Node.js is missing, and resume PDF compilation
reports the missing Tectonic toolchain only when it is actually used.

The optional AI workers run on a selectable runtime. Codex and Claude are both
supported and are chosen in **Agent control → AI limit & worker history → AI
runtime**, or with `CAREER_AI_RUNTIME=claude`. Read
[career-dashboard/docs/AI-RUNTIMES.md](career-dashboard/docs/AI-RUNTIMES.md)
before changing anything in `career-dashboard/services/ai_runtime.py`.

Mailbox review is the one worker Claude cannot run: it needs Codex's connected
Gmail read tools, so email syncs stay on Codex regardless of the selected
runtime. Do not add a mailbox integration for another runtime without being
asked.

Run `./Check Workspace.command` after code changes, and use a disposable
workspace for anything that mutates state.
