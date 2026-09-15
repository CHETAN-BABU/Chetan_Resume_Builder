#!/usr/bin/env python3
"""Validate Chetan's profile, agent guardrails, workflow paths, and base resume."""

from __future__ import annotations

import ast
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ERRORS: list[str] = []
WARNINGS: list[str] = []

REQUIRED_JOB_ARTIFACTS = (
    "job-description.md",
    "evaluation.md",
    "company-research.md",
    "evidence-map.yml",
    "resume.tex",
    "resume.pdf",
    "resume-preview/page-01.png",
    "resume-preview/page-02.png",
    "qa.json",
)


def fail(message: str) -> None:
    ERRORS.append(message)


def warn(message: str) -> None:
    WARNINGS.append(message)


def read(relative_path: str, base: Path = None) -> str:
    path = (base or ROOT) / relative_path
    if not path.is_file():
        fail(f"Missing required file: {relative_path}")
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        fail(f"Not UTF-8: {relative_path} ({exc})")
        return ""


def validate_yaml(relative_path: str) -> None:
    load_yaml_mapping(relative_path)


def load_yaml_mapping(relative_path: str) -> dict[str, Any] | None:
    from validate_resume import load_yaml
    try:
        return load_yaml(ROOT / relative_path)
    except (RuntimeError, OSError, ValueError) as exc:
        fail(f"Unable to inspect YAML: {relative_path} ({exc})")
        return None


def strip_latex_comments(source: str) -> str:
    lines = []
    for line in source.splitlines():
        match = re.search(r"(?<!\\)%", line)
        lines.append(line[: match.start()] if match else line)
    return "\n".join(lines)


def latex_braces_balanced(source: str) -> bool:
    depth = 0
    escaped = False
    for character in strip_latex_comments(source):
        if escaped:
            escaped = False
            continue
        if character == "\\":
            escaped = True
        elif character == "{":
            depth += 1
        elif character == "}":
            depth -= 1
            if depth < 0:
                return False
    return depth == 0


def validate_skill(relative_dir: str, ui_metadata: bool = True, base: Path = None) -> None:
    base = base or ROOT
    skill_dir = base / relative_dir
    source = read(f"{relative_dir}/SKILL.md", base)
    match = re.match(r"^---\n(.*?)\n---\n", source, re.DOTALL)
    if not match:
        fail(f"Invalid or missing skill frontmatter: {relative_dir}/SKILL.md")
        return
    frontmatter = match.group(1)
    name_match = re.search(r"^name:\s*([a-z0-9-]+)\s*$", frontmatter, re.MULTILINE)
    if not name_match:
        fail(f"Skill name must use lowercase hyphen-case: {relative_dir}/SKILL.md")
    elif name_match.group(1) != skill_dir.name:
        fail(f"Skill name/folder mismatch: {name_match.group(1)} != {skill_dir.name}")
    if not re.search(r"^description:\s*\S", frontmatter, re.MULTILINE):
        fail(f"Skill description missing: {relative_dir}/SKILL.md")
    if ui_metadata and not (skill_dir / "agents/openai.yaml").is_file():
        fail(f"Skill UI metadata missing: {relative_dir}/agents/openai.yaml")


def validate_python() -> None:
    for path in ROOT.rglob("*.py"):
        if set(path.relative_to(ROOT).parts) & {".venv", "__pycache__", "output", "docs"}:
            continue
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (SyntaxError, UnicodeDecodeError) as exc:
            fail(f"Python parse failed: {path.relative_to(ROOT)} ({exc})")


def validate_text_identity() -> None:
    other_candidate_names = (
        "su" + "deep",
        "su" + "dip",
        "santi" + "ago",
        "santi" + "fer",
    )
    other_person = re.compile(
        rf"\b({'|'.join(re.escape(name) for name in other_candidate_names)})\b",
        re.IGNORECASE,
    )
    text_suffixes = {".md", ".txt", ".tex", ".yml", ".yaml", ".json", ".csv", ".tsv", ".py"}
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(ROOT)
        if (
            bool(set(relative.parts) & {".venv", "output", "docs"})
            or "__pycache__" in relative.parts
            or relative == Path("scripts/validate_workspace.py")
            or path.suffix.lower() not in text_suffixes
        ):
            continue
        try:
            source = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            fail(f"Non-UTF-8 active file: {relative}")
            continue
        if other_person.search(source) or other_person.search(path.name):
            fail(f"Another candidate identity appears in active content: {relative}")


def validate_profile() -> None:
    profile = read("config/profile.yml")
    required = [
        "candidate_revision",
        "Chetan Babu M",
        "Data Analyst",
        "BI Analyst",
        "BI Developer",
        "Junior Data Scientist",
        "AI Engineer",
        "never_position_as",
        "claim_policy",
        "project_selection",
        "required_selected_projects: 2",
        "resume_contract",
        "required_pages: 2",
        "batch_contract",
    ]
    for value in required:
        if value not in profile:
            fail(f"Profile missing required guardrail/value: {value}")

    for agent_path in (
        ".github/agents/resume-builder.agent.md",
        ".github/agents/ireland-job-hunter.agent.md",
    ):
        agent = read(agent_path)
        for value in ("Chetan Babu M", "Data Analyst", "BI Analyst", "Data Scientist", "AI Engineer"):
            if value not in agent:
                fail(f"{agent_path} missing candidate boundary: {value}")

    resume_agent = read(".github/agents/resume-builder.agent.md")
    for value in (
        "context/evidence.yml",
        "exactly two",
        "exactly two",
        "supported requirement coverage",
        "scripts/validate_resume.py",
    ):
        if value.lower() not in resume_agent.lower():
            fail(f"Resume Builder missing end-to-end contract: {value}")


def validate_evidence_registry() -> None:
    evidence = read("context/evidence.yml")
    registry = load_yaml_mapping("context/evidence.yml")
    if registry is None:
        return

    claims = registry.get("claims")
    projects = registry.get("projects")
    not_resume_ready = registry.get("not_resume_ready", [])
    if not isinstance(claims, list):
        fail("Evidence registry claims must be a list")
        claims = []
    if not isinstance(projects, list):
        fail("Evidence registry projects must be a list")
        projects = []
    if not isinstance(not_resume_ready, list):
        fail("Evidence registry not_resume_ready must be a list")
        not_resume_ready = []

    entries: list[tuple[str, dict[str, Any]]] = []
    for section_name, section in (
        ("claims", claims),
        ("projects", projects),
        ("not_resume_ready", not_resume_ready),
    ):
        for index, item in enumerate(section, start=1):
            if not isinstance(item, dict):
                fail(f"Evidence registry {section_name}[{index}] must be a mapping")
                continue
            entries.append((section_name, item))

    ids = [str(item.get("id", "")) for _, item in entries]
    malformed_ids = sorted(
        value or "<missing>"
        for value in ids
        if not re.fullmatch(r"[A-Z0-9-]+", value)
    )
    if malformed_ids:
        fail(f"Malformed evidence IDs: {', '.join(malformed_ids)}")
    if len(ids) != len(set(ids)):
        duplicates = sorted({value for value in ids if ids.count(value) > 1})
        fail(f"Duplicate evidence IDs: {', '.join(duplicates)}")

    required_projects = {
        "PROJ-AZ-RECON",
        "PROJ-AZ-MIGRATION",
        "PROJ-NIQ-POC",
        "PROJ-AZ-EXEC",
        "PROJ-NIQ-REPORTING",
        "PROJ-MSC-FRAUD",
        "PROJ-KPMG-FORAGE",
        "PROJ-RAG-CHATBOT",
        "PROJ-SECOM-FAULT-DETECTION",
        "PROJ-FAANG-PCA",
        "PROJ-CLUSTERING-DBSCAN",
        "PROJ-EU-COMPLIANCE-RAG",
        "PROJ-POWERBI-PORTFOLIO",
        "PROJ-BLOGBOARD",
    }
    project_ids = {
        str(item.get("id"))
        for item in projects
        if isinstance(item, dict) and item.get("id")
    }
    missing = required_projects - project_ids
    if missing:
        fail(f"Evidence registry missing resume-ready project IDs: {', '.join(sorted(missing))}")

    for section_name, section in (("claim", claims), ("project", projects)):
        for item in section:
            if not isinstance(item, dict):
                continue
            item_id = str(item.get("id", "<missing>"))
            source_refs = item.get("source_refs")
            if (
                not isinstance(source_refs, list)
                or not source_refs
                or any(not isinstance(ref, str) or not ref.strip() for ref in source_refs)
            ):
                fail(f"Evidence {section_name} {item_id} needs non-empty source_refs")

    required_resume_content_keys = {"title", "context", "bullets"}
    for project in projects:
        if not isinstance(project, dict):
            continue
        project_id = str(project.get("id", "<missing>"))
        resume_content = project.get("resume_content")
        if not isinstance(resume_content, dict):
            fail(f"Evidence project {project_id} needs resume_content mapping")
            continue
        actual_keys = set(resume_content)
        if actual_keys != required_resume_content_keys:
            missing_keys = sorted(required_resume_content_keys - actual_keys)
            extra_keys = sorted(actual_keys - required_resume_content_keys)
            details = []
            if missing_keys:
                details.append(f"missing {', '.join(missing_keys)}")
            if extra_keys:
                details.append(f"unexpected {', '.join(extra_keys)}")
            fail(
                f"Evidence project {project_id} resume_content must contain exactly "
                f"title, context, bullets ({'; '.join(details)})"
            )
            continue
        for field in ("title", "context"):
            value = resume_content.get(field)
            if not isinstance(value, str) or not value.strip():
                fail(f"Evidence project {project_id} resume_content.{field} must be non-empty text")
        bullets = resume_content.get("bullets")
        if (
            not isinstance(bullets, list)
            or not 2 <= len(bullets) <= 3
            or any(not isinstance(bullet, str) or not bullet.strip() for bullet in bullets)
        ):
            fail(
                f"Evidence project {project_id} resume_content.bullets "
                "must contain 2-3 non-empty strings"
            )

    profile = load_yaml_mapping("config/profile.yml")
    revision = registry.get("candidate_revision")
    if not isinstance(revision, str) or not revision.strip():
        fail("Evidence registry needs a non-empty candidate_revision")
    elif profile is not None and revision != profile.get("candidate_revision"):
        fail("Evidence registry candidate_revision must match config/profile.yml")

    for value in (
        'client_name_disclosure: approved_by_user_2026-09-09',
        "ownership_rule",
        "approved_external_use",
        "prohibited",
        "immutable_across_resumes",
    ):
        if value not in evidence:
            fail(f"Evidence registry missing contract value: {value}")


def validate_artifact_contract() -> None:
    expected = list(REQUIRED_JOB_ARTIFACTS)
    profile = load_yaml_mapping("config/profile.yml")
    if profile is not None:
        batch_contract = profile.get("batch_contract")
        actual = (
            batch_contract.get("required_artifacts")
            if isinstance(batch_contract, dict)
            else None
        )
        if actual != expected:
            fail(
                "config/profile.yml batch_contract.required_artifacts must exactly match "
                "the canonical nine per-job artifact paths"
            )

    template = load_yaml_mapping("templates/batch.example.yml")
    if template is not None and template.get("required_artifacts") != expected:
        fail(
            "templates/batch.example.yml required_artifacts must exactly match "
            "the canonical nine per-job artifact paths"
        )


def validate_resume() -> None:
    resume = read("templates/resume-base.tex")
    if not resume:
        return
    hyperref_loads = re.findall(
        r"\\usepackage(?:\[[^\]]*\])?\{hyperref\}",
        strip_latex_comments(resume),
    )
    if len(hyperref_loads) != 1:
        fail(f"Resume must load hyperref exactly once; found {len(hyperref_loads)}")
    if r"\documentclass[a4paper,10pt]{article}" not in resume:
        fail("Resume must use the A4 10pt base document class")
    if not resume.rstrip().endswith(r"\end{document}"):
        fail("Resume does not end with \\end{document}")
    if not latex_braces_balanced(resume):
        fail("Resume has unbalanced LaTeX braces")

    required = (
        "Chetan Babu M",
        "Data Analyst",
        "BI Developer",
        "300+",
        "160 Power BI reports",
        "In Progress",
        "SRM Institute of Science and Technology",
        "Jun 2019 -- May 2023",
        "9.4/10",
        "AstraZeneca -- pharmaceutical client",
        "NielsenIQ -- reporting engagement",
        "Hindustan Unilever -- Power BI enhancement engagement",
        r"\section{Selected Project}",
        r"\newcommand{\SelectedProjectID}{PROJ-AZ-RECON}",
        "pdfauthor={Chetan Babu M}",
    )
    for value in required:
        if value not in resume:
            fail(f"Resume missing required supported content: {value}")

    unsafe = (
        "100+ reports",
        "single month",
        "independently designed",
        "led the migration",
        "$5M",
        "5 Million",
        "close to 3 years",
        "zero data discrepancies",
        "recognized for excellence",
        "interactive KPIs",
        "NSS Student Coordinator",
        "References available upon request",
    )
    for value in unsafe:
        if value.lower() in resume.lower():
            fail(f"Resume contains unsafe or conflicting claim: {value}")

    if len(re.findall(r"\\section\{Selected Project\}", resume)) != 1:
        fail("Resume must contain exactly one Selected Project section")
    if len(re.findall(r"\\newcommand\{\\SelectedProjectID\}\{[^{}]+\}", resume)) != 1:
        fail("Resume must declare exactly one SelectedProjectID")
    if len(re.findall(r"\\newcommand\{\\SecondProjectID\}\{[^{}]+\}", resume)) != 1:
        fail("Resume must declare a second project")
    if resume.count(r"\newpage") != 1:
        fail("Resume must contain exactly one explicit page break")
    if r"\documentclass[a4paper,10pt]{article}" not in resume:
        fail("Resume must preserve the fixed A4 10pt contract")

    pdf = ROOT / "output/base/Chetan_Babu_M_Resume.pdf"
    source = ROOT / "templates/resume-base.tex"
    if pdf.is_file() and pdf.stat().st_mtime < source.stat().st_mtime:
        fail("Base resume PDF is stale; recompile it from templates/resume-base.tex")


def validate_runtimes() -> None:
    """The selectable AI runtimes and the Claude workspace files must stay intact."""
    runtime = read("services/ai_runtime.py")
    for required in ("class CodexRuntime", "class ClaudeRuntime", "BUILT_IN = [CodexRuntime, ClaudeRuntime]"):
        if required not in runtime:
            fail(f"AI runtime registry is missing {required!r}: services/ai_runtime.py")
    if "MAIL_NEEDS_CODEX" not in runtime:
        fail("Mailbox work must still be reported as Codex-only: services/ai_runtime.py")
    agents = read("services/agents.py")
    if 'shutil.which("codex")' not in agents:
        fail("The original Codex invocation must remain in services/agents.py")
    if "self.runtimes" not in agents:
        fail("services/agents.py must dispatch optional AI work through the runtime registry")
    read("docs/AI-RUNTIMES.md")
    read("CLAUDE.md")

    workspace_root = ROOT.parent
    read("CLAUDE.md", workspace_root)
    settings = read(".claude/settings.json", workspace_root)
    try:
        permissions = json.loads(settings).get("permissions", {})
    except json.JSONDecodeError as exc:
        fail(f"Invalid JSON: .claude/settings.json ({exc})")
        permissions = {}
    if not any("backup/" in rule for rule in permissions.get("deny", [])):
        fail("Claude settings must keep preserved backups read-only: .claude/settings.json")
    validate_skill(".claude/skills/verify-job-url", ui_metadata=False, base=workspace_root)
    canonical = re.search(r"^description:\s*(.+)$",
                          read(".agents/skills/verify-job-url/SKILL.md"), re.MULTILINE)
    mirror = re.search(r"^description:\s*(.+)$",
                       read(".claude/skills/verify-job-url/SKILL.md", workspace_root), re.MULTILINE)
    if canonical and mirror and canonical.group(1).strip() != mirror.group(1).strip():
        fail("The Claude skill mirror has drifted from .agents/skills/verify-job-url/SKILL.md")


def validate_paths() -> None:
    for retired in (
        "jobs/ireland/Version1",
        "jobs/ireland/Version2",
        "tmp_filter.py",
        "jobs/ireland/webscrppng.csv",
    ):
        if (ROOT / retired).exists():
            fail(f"Retired AI-profile artifact still exists: {retired}")



def main() -> int:
    for required in (
        "AGENTS.md",
        "config/profile.yml",
        "config/portals.yml",
        "context/sources/career.md",
        "context/PROFILE.md",
        "context/evidence.yml",
        "templates/resume-base.tex",
        "context/PROFILE-NOTES.md",
        "workflows/modes/_shared.md",
        "workflows/modes/_profile.md",
        "workflows/modes/resume.md",
        "workflows/modes/quality.md",
        "workflows/modes/batch-resumes.md",
        "DATA_CONTRACT.md",
        "output/README.md",
        "templates/batch.example.yml",
        "data/application-tracker.md",
    ):
        read(required)

    validate_yaml("config/profile.yml")
    validate_yaml("config/portals.yml")
    validate_yaml("context/evidence.yml")
    validate_yaml("templates/batch.example.yml")
    validate_yaml(".agents/skills/verify-job-url/agents/openai.yaml")
    validate_skill(".agents/skills/verify-job-url")
    validate_python()
    validate_text_identity()
    validate_profile()
    validate_evidence_registry()
    validate_artifact_contract()
    validate_resume()
    validate_runtimes()
    validate_paths()

    for message in WARNINGS:
        print(f"WARN: {message}")
    if ERRORS:
        for message in ERRORS:
            print(f"FAIL: {message}")
        print(f"\nWorkspace validation failed with {len(ERRORS)} error(s).")
        return 1
    print("PASS: Chetan profile, agents, workflows, skill, paths, and base resume are consistent.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
