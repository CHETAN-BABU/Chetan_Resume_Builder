# Selectable AI runtimes

Updated 15 September 2026. The application's own work is deterministic Python:
saving instructions, tracking edits, ranking projects, fitting PDFs, scoring
document vocabulary and monitoring runs all cost nothing and need no model.
Only the optional workers listed in
[AGENT-ARCHITECTURE.md](AGENT-ARCHITECTURE.md) call a model, and each of those
calls goes through one **runtime**.

`services/ai_runtime.py` holds the registry. A runtime receives a prompt, an
output schema and two flags — whether the worker needs public web sources, and
whether it needs connected mailbox read tools — and returns the parsed
structured result or raises. It never reads candidate files, mail or chat
history: every payload is assembled by the caller.

## What is installed

| Runtime | ID | Offline workers | Public web research | Mailbox review |
|---|---|---|---|---|
| Codex | `codex` | yes | yes | yes |
| Claude | `claude` | yes | yes | no |

Codex is the original implementation and its call is unchanged: the registry
only detects it and dispatches to the existing function in `services/agents.py`.
Claude runs Claude Code in headless mode (`--print`) with a validated output
schema.

## Choosing one

Agent control → **AI limit & worker history** → **AI runtime**. `Automatic` uses
the first installed runtime, which keeps an existing Codex machine on Codex.
Selecting a runtime explicitly pins it, including when it is not installed, so
the error names what to install.

Equivalent controls outside the UI:

```sh
career-dashboard/.venv/bin/python career-dashboard/scripts/workspace.py agent-control
```

| Setting | Effect |
|---|---|
| `CAREER_AI_RUNTIME` | `auto`, `codex` or `claude`. Overrides the saved preference for one process. |
| `CAREER_CLAUDE_BIN` | Path to the `claude` executable when it is not on `PATH`. |
| `CAREER_CLAUDE_MODEL` | Model for the Claude runtime. Default `claude-sonnet-5`; any model its CLI accepts works. |
| `CAREER_CLAUDE_MAX_USD` | Optional per-invocation spend ceiling. Unset means no ceiling, matching Codex. |
| `CAREER_AI_RUNTIME_PLUGINS` | Comma-separated `module:callable` entries that register another provider's runtime. |

The model and the ceiling are also stored per runtime in the `ai_runtime`
preference, so the UI's **Model** field survives restarts.

## Mailbox review stays on Codex

The email worker is the only one that needs connected Gmail read tools, and only
the Codex runtime exposes them. Mailbox calls are routed to Codex whatever the
selection is; if Codex is not installed, the worker reports that and preserves
the last successful sync and all saved email evidence. Selecting Claude never
silently changes what email evidence exists. No mailbox integration exists for
any other runtime, and none should be added without being asked.

## Isolation on the Claude runtime

Every Claude worker is a fresh, single-turn, non-persisted session:

- `--setting-sources ""`, `--strict-mcp-config` and `--disable-slash-commands`:
  no project settings, no MCP servers and no skills can answer part of a prompt.
- `--system-prompt`: a short worker instruction replaces the coding-assistant
  preamble. Input is data, never instructions; limitations are stated rather
  than guessed.
- `--tools ""` for offline workers. Research workers get exactly `WebSearch` and
  `WebFetch`; no shell, file or code tool is ever offered, and a blocked tool
  fails the run instead of producing a result that was never researched.
- `--no-session-persistence`, a temporary working directory, and a child
  environment stripped of the parent session's `CLAUDE_CODE_*` variables.
- `--json-schema`: the same output schema the worker already defined. A result
  missing any required field is rejected and never saved.

## Saved results are per runtime

The AI cache keys on worker version, prompt, schema and options. The runtime is
part of that key for everything except Codex, whose keys are left in their
original shape so results saved by the existing workspace stay reusable.
Switching runtime therefore never reuses another runtime's answer, and never
discards one either. Cache lookup still happens before budget reservation, so
saved results remain available with a daily limit of 0.

## Adding another provider

Subclass `Runtime` in your own module, set `id`, `name`, `detail`, `web` and
`mail`, implement `locate()` and `invoke(prompt, schema, apps, web)`, then point
`CAREER_AI_RUNTIME_PLUGINS` at a callable that returns it. Raise `ValueError`
with a sentence the user can act on; the orchestrator records it as a failed run
and infers nothing from the failure. Return a dict matching the schema, or raise
— never a partial result.
