"""Runtime selection, isolation and failure reporting for the optional AI workers."""
import json
import sys
import types
import pytest
from test_career_workspace import workspace, add
from test_workspace_v2 import service
from services.agents import AgentRunner, REPORT_SCHEMA
from services.ai_runtime import (
    AIRuntimes,
    ClaudeRuntime,
    CodexRuntime,
    Runtime,
    child_env,
    version_key,
)

REPORT = {"summary": "ok", "report": "Saved result", "sources": [], "limitations": []}


class Fake(Runtime):
    def __init__(self, id, name="Fake", available=True, mail=False, web=True):
        super().__init__(None)
        self.id, self.name, self.mail, self.web = id, name, mail, web
        self.detail = name + " is not installed."
        self.installed = available
        self.calls = []

    def locate(self):
        return "/fake/" + self.id if self.installed else None

    def invoke(self, prompt, schema, apps=False, web=True):
        if not self.installed:
            raise ValueError(self.detail)
        self.calls.append({"prompt": prompt, "apps": apps, "web": web})
        return dict(REPORT)


def installed(monkeypatch, codex=True, claude=True):
    monkeypatch.setattr(CodexRuntime, "locate", lambda self: "/fake/codex" if codex else None)
    monkeypatch.setattr(ClaudeRuntime, "locate", lambda self: "/fake/claude" if claude else None)
    monkeypatch.delenv("CAREER_AI_RUNTIME", raising=False)


def runner_with_recorder(service):
    seen = []

    def execute(prompt, schema, **options):
        seen.append(options)
        return dict(REPORT)

    runner = AgentRunner(service, execute)
    return runner, seen


def test_automatic_selection_prefers_codex_and_keeps_existing_cache_keys(service, monkeypatch):
    installed(monkeypatch)
    runner, seen = runner_with_recorder(service)
    assert runner.runtimes.status()["active"] == "codex"
    runner.cached("public role", REPORT_SCHEMA, web=False)
    # No runtime field: results saved by the original Codex workspace stay reusable.
    assert seen == [{"web": False}]


def test_selecting_claude_routes_calls_and_separates_saved_results(service, monkeypatch):
    installed(monkeypatch)
    runner, seen = runner_with_recorder(service)
    runner.cached("public role", REPORT_SCHEMA, web=False)
    runner.runtimes.configure(runtime="claude")
    assert runner.runtimes.status()["active_name"] == "Claude"
    runner.cached("public role", REPORT_SCHEMA, web=False)
    assert seen == [{"web": False}, {"web": False, "runtime": "claude"}]
    # Same prompt, different runtime: the earlier Codex answer is not reused.
    assert runner.cache.stats()["cache_hits"] == 0
    runner.cached("public role", REPORT_SCHEMA, web=False)
    assert len(seen) == 2 and runner.cache.stats()["cache_hits"] == 1


def test_environment_override_wins_over_the_saved_preference(service, monkeypatch):
    installed(monkeypatch)
    runner = AgentRunner(service, lambda *a, **k: dict(REPORT))
    runner.runtimes.configure(runtime="codex")
    monkeypatch.setenv("CAREER_AI_RUNTIME", "claude")
    assert runner.runtimes.selected() == "claude"
    monkeypatch.setenv("CAREER_AI_RUNTIME", "not-a-runtime")
    assert runner.runtimes.selected() == "auto"


def test_automatic_selection_falls_through_to_an_installed_runtime(service, monkeypatch):
    installed(monkeypatch, codex=False)
    runner = AgentRunner(service, lambda *a, **k: dict(REPORT))
    assert runner.runtimes.status()["active"] == "claude"
    installed(monkeypatch, codex=False, claude=False)
    status = AgentRunner(service, lambda *a, **k: dict(REPORT)).runtimes.status()
    assert status["active"] == "codex" and status["active_available"] is False
    assert "sign in" in status["requirement"]


def test_mailbox_work_stays_on_codex_even_when_claude_is_selected(service, monkeypatch):
    installed(monkeypatch)
    runner, seen = runner_with_recorder(service)
    runner.runtimes.configure(runtime="claude")
    assert runner.runtime_for(apps=True).id == "codex"
    runner.cached("mailbox", REPORT_SCHEMA, apps=True, web=False, cacheable=False)
    # Routed to the mail-capable runtime, so the key stays in the Codex shape.
    assert seen == [{"apps": True, "web": False}]
    assert runner.runtimes.status()["mail_runtime"] == "codex"


def test_claude_refuses_mailbox_work_and_names_the_runtime_that_can(monkeypatch):
    installed(monkeypatch)
    claude = ClaudeRuntime(None)
    with pytest.raises(ValueError, match="Codex runtime"):
        claude.invoke("prompt", REPORT_SCHEMA, apps=True)
    status = AIRuntimes(None, [Fake("claude", "Claude")]).status()
    assert status["mail_runtime"] == "" and "mailbox" in status["mail_note"]


def test_claude_offers_only_public_reading_tools(monkeypatch):
    monkeypatch.delenv("CAREER_CLAUDE_MODEL", raising=False)
    monkeypatch.delenv("CAREER_CLAUDE_MAX_USD", raising=False)
    claude = ClaudeRuntime(None)
    offline = claude.command("/fake/claude", REPORT_SCHEMA, web=False)
    research = claude.command("/fake/claude", REPORT_SCHEMA, web=True)
    assert offline[offline.index("--tools") + 1] == ""
    assert research[research.index("--tools") + 1] == "WebSearch,WebFetch"
    assert research[research.index("--allowed-tools") + 1 : research.index("--allowed-tools") + 3] == [
        "WebSearch",
        "WebFetch",
    ]
    for command in (offline, research):
        assert "--no-session-persistence" in command
        assert "--strict-mcp-config" in command
        assert command[command.index("--setting-sources") + 1] == ""
        assert command[command.index("--permission-prompts") + 1] == "none"
        assert json.loads(command[command.index("--json-schema") + 1]) == REPORT_SCHEMA
        assert command[command.index("--model") + 1] == "claude-sonnet-5"
        assert "--max-budget-usd" not in command
        for tool in ("Bash", "Edit", "Write", "Read"):
            assert tool not in " ".join(command)
    monkeypatch.setenv("CAREER_CLAUDE_MODEL", "claude-opus-5")
    monkeypatch.setenv("CAREER_CLAUDE_MAX_USD", "1.5")
    capped = ClaudeRuntime(None).command("/fake/claude", REPORT_SCHEMA, web=False)
    assert capped[capped.index("--model") + 1] == "claude-opus-5"
    assert capped[capped.index("--max-budget-usd") + 1] == "1.5"


def test_claude_reads_the_structured_result(monkeypatch):
    claude = ClaudeRuntime(None)
    payload = {"subtype": "success", "is_error": False, "structured_output": REPORT,
               "result": json.dumps(REPORT)}
    assert claude.read(0, json.dumps(payload), "", ) == REPORT
    text_only = dict(payload, structured_output=None)
    assert claude.read(0, json.dumps(text_only), "") == REPORT


@pytest.mark.parametrize(
    "code,stdout,expected",
    [
        (1, "", "signed in"),
        (0, "", "signed in"),
        (0, "not json at all", "could not read"),
        (0, json.dumps({"is_error": True, "subtype": "error_during_execution",
                        "result": "usage limit reached"}), "usage limit reached"),
        (0, json.dumps({"subtype": "success", "is_error": False,
                        "permission_denials": [{"tool_name": "WebSearch"}]}), "WebSearch"),
        (0, json.dumps({"subtype": "success", "is_error": False, "result": "plain sentence"}),
         "did not return the requested structured result"),
    ],
)
def test_claude_reports_failures_without_inventing_a_result(code, stdout, expected):
    with pytest.raises(ValueError, match=expected):
        ClaudeRuntime(None).read(code, stdout, "runtime said something")


def test_claude_is_found_through_an_explicit_path_override(monkeypatch, tmp_path):
    binary = tmp_path / "claude"
    binary.write_text("#!/bin/sh\n")
    monkeypatch.setenv("CAREER_CLAUDE_BIN", str(binary))
    assert ClaudeRuntime(None).locate() == str(binary)
    monkeypatch.setenv("CAREER_CLAUDE_BIN", str(tmp_path / "missing"))
    monkeypatch.setattr("shutil.which", lambda name: None)
    monkeypatch.setattr("pathlib.Path.home", staticmethod(lambda: tmp_path))
    assert ClaudeRuntime(None).locate() is None
    assert version_key("2.10.3") > version_key("2.9.9")


def test_a_registered_plugin_runtime_becomes_selectable(service, monkeypatch):
    module = types.ModuleType("career_test_runtime")
    module.runtime = lambda services: Fake("other", "Other provider")
    monkeypatch.setitem(sys.modules, "career_test_runtime", module)
    monkeypatch.setenv("CAREER_AI_RUNTIME_PLUGINS", "career_test_runtime")
    monkeypatch.delenv("CAREER_AI_RUNTIME", raising=False)
    runtimes = AIRuntimes(service)
    assert [r["id"] for r in runtimes.status()["runtimes"]] == ["codex", "claude", "other"]
    runtimes.configure(runtime="other")
    assert runtimes.resolve().id == "other"
    assert runtimes.resolve(apps=True).id == "codex"
    with pytest.raises(ValueError, match="available AI runtime"):
        runtimes.configure(runtime="nothing-installed")


def test_configure_saves_the_runtime_and_its_model(service, monkeypatch):
    installed(monkeypatch)
    runtimes = AIRuntimes(service)
    runtimes.configure(runtime="claude", model="claude-opus-5")
    assert service.pref("ai_runtime") == {"runtime": "claude", "claude": {"model": "claude-opus-5"}}
    assert AIRuntimes(service).resolve().model() == "claude-opus-5"
    assert any(e["action"] == "ai_runtime_updated" for e in service.w.activity())


def test_worker_processes_drop_parent_session_variables(monkeypatch):
    monkeypatch.setenv("CLAUDE_CODE_SESSION_ID", "parent")
    monkeypatch.setenv("CLAUDECODE", "1")
    monkeypatch.setenv("PATH", "/usr/bin")
    env = child_env()
    assert "CLAUDE_CODE_SESSION_ID" not in env and "CLAUDECODE" not in env
    assert env["PATH"] == "/usr/bin"
