#!/usr/bin/env python3
"""Compile and fail-closed validate Chetan's base or tailored LaTeX resume."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BASE_TEMPLATE = (ROOT / "templates/resume-base.tex").resolve()
EVIDENCE_PATH = ROOT / "context/evidence.yml"
PDF_INSPECTOR = ROOT / "scripts/pdf_inspect.swift"


REQUIRED_SECTIONS = (
    "Professional Summary",
    "Core Skills",
    "Professional Experience",
    "Selected Project",
    "Education",
    "Certifications",
    "Technical Skills",
)

UNSAFE_PATTERNS = {
    "unsupported contract-causality claim": r"(?i)(?:\$|USD\s*)5\s*(?:M|million)",
    "unsupported monthly report count": r"(?i)100\+\s+reports",
    "unsupported migration leadership": r"(?i)\bled the (?:Redshift-to-Snowflake )?migration\b",
    "unsupported independent ownership": r"(?i)\bindependently (?:owned|designed|developed|built)\b",
    "unsupported absolute quality claim": r"(?i)\bzero (?:data )?(?:defects|discrepancies|errors)\b",
    "unsupported work-right claim": r"(?i)\b(?:unrestricted work|no sponsorship required|full work authorization)\b",
    "unsupported certification praise": r"(?i)recognized for excellence",
    "unsupported HUL scope": r"(?i)interactive KPIs",
    "unsupported extracurricular claim": r"(?i)\b(?:NSS Student Coordinator|beach cleaning|tree plantation)\b",
    "prohibited filler": r"(?i)references available upon request",
    "unsupported unregistered AI/engineering technology": r"(?i)\b(?:LlamaIndex|PyTorch|TensorFlow|Databricks|Apache Spark)\b",
    "unsupported production AI/MLOps claim": r"(?i)\b(?:professional (?:AI|GenAI|ML|MLOps) experience|production (?:RAG|LLM|GenAI) (?:system|platform|deployment)|MLOps Engineer|deployed (?:on|to) Kubernetes)\b",
    "unconfirmed SQL dialect": r"(?i)\b(?:MySQL|SQL Server|PostgreSQL)\b",
}

PLACEHOLDER_PATTERNS = {
    "double-brace placeholder": r"\{\{[^{}]+\}\}",
    "angle placeholder": r"<(?:COMPANY|ROLE|DATE|INSERT|TODO)[^>]*>",
    "unfinished marker": r"(?i)\b(?:TBD|TODO|FIXME|YOUR COMPANY|INSERT HERE)\b",
}

PROHIBITED_LAYOUT_PATTERNS = {
    "multi-column package/environment": r"(?i)\\(?:usepackage\{(?:multicol|paracol)\}|begin\{multicols?\})",
    "sidebar/minipage layout": r"\\begin\{minipage\}",
    "raster or vector image": r"\\includegraphics",
    "font below contract": r"\\(?:tiny|scriptsize|footnotesize|small)\b",
    "manual font shrinking": r"\\fontsize\s*\{",
    "geometry override": r"\\geometry\s*\{",
    "margin mutation": r"\\(?:addtolength|setlength)\s*\{\\(?:oddsidemargin|evensidemargin|textwidth|topmargin|textheight)",
    "line-spread override": r"\\linespread\s*\{",
}

ALLOWED_VISIBLE_NUMBERS = {
    "1",
    "2",
    "3",
    "5",
    "6",
    "50",
    "160",
    "300",
    "14,964",
    "16",
    "16.3",  # PROJ-MSC-FRAUD: registered independent-test precision.
    "90.6",
    "2019",
    "9.4",
    "10",
    "2023",
    "2025",
    "2026",
    "0.001",
    "0.01",
    "0.0183",
    "0.05",
    "0.069",
    "0.173",
    "0.1795",
    "0.20",
    "0.25",
    "0.535",
    "0.814",
    "0.839",
    "1,115",
    "1,173",
    "1,567",
    "2,000",
    "7.45",
    "14",
    "20",
    "25.6",
    "26",
    "51,290",
    "60",
    "60.3",
    "80",
    "90",
    "95",
    "162",
    "200",
    "305",
    "446",
    "516",
    "590",
    "2008",
    "2022",
    "10,000",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def strip_latex_comments(source: str) -> str:
    lines: list[str] = []
    for line in source.splitlines():
        index = None
        escaped = False
        for position, character in enumerate(line):
            if character == "%" and not escaped:
                index = position
                break
            escaped = character == "\\" and not escaped
            if character != "\\":
                escaped = False
        lines.append(line[:index] if index is not None else line)
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


def approximate_visible_words(source: str) -> int:
    text = strip_latex_comments(source)
    text = re.sub(r"\\(?:href|roleheading|clientheading)\s*\{([^{}]*)\}\s*\{([^{}]*)\}", r"\1 \2", text)
    text = re.sub(r"\\[A-Za-z@]+(?:\[[^\]]*\])?", " ", text)
    text = text.replace(r"\&", "&").replace(r"\%", "%").replace(r"\textbar{}", "|")
    text = re.sub(r"[{}]", " ", text)
    text = re.sub(r"[^A-Za-z0-9+#/&.-]+", " ", text)
    return len(re.findall(r"\b[A-Za-z0-9][A-Za-z0-9+#/&.-]*\b", text))


def extract_zero_argument_macros(source: str) -> dict[str, str]:
    """Extract simple no-argument newcommands while preserving nested braces."""
    commands: dict[str, str] = {}
    pattern = re.compile(r"\\newcommand\{\\([A-Za-z@]+)\}")
    for match in pattern.finditer(source):
        position = match.end()
        while position < len(source) and source[position].isspace():
            position += 1
        if position >= len(source) or source[position] == "[" or source[position] != "{":
            continue
        depth = 0
        escaped = False
        end = None
        for index in range(position, len(source)):
            character = source[index]
            if escaped:
                escaped = False
                continue
            if character == "\\":
                escaped = True
                continue
            if character == "{":
                depth += 1
            elif character == "}":
                depth -= 1
                if depth == 0:
                    end = index
                    break
        if end is not None:
            commands[match.group(1)] = source[position + 1 : end]
    return commands


def expand_zero_argument_macros(source: str, body: str) -> str:
    """Expand simple no-argument newcommands for source-density estimates."""
    commands = extract_zero_argument_macros(source)
    expanded = body
    for name, value in sorted(commands.items(), key=lambda item: len(item[0]), reverse=True):
        expanded = re.sub(rf"\\{re.escape(name)}\b", lambda _: value, expanded)
    return expanded


def normalize_latex_text(value: str) -> str:
    # Callers pass an already isolated construct or plain registry text. Do not
    # treat a literal percent in registry prose as the start of a LaTeX comment.
    text = value
    replacements = {
        r"\%": "%",
        r"\&": "&",
        r"\_": "_",
        r"\textbar{}": "|",
        "--": "-",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = re.sub(r"\\(?:textbf|textit|emph)\{([^{}]*)\}", r"\1", text)
    text = re.sub(r"\\[A-Za-z@]+(?:\[[^\]]*\])?", " ", text)
    text = text.replace("{", " ").replace("}", " ")
    return re.sub(r"\s+", " ", text).strip()


def evidence_ids_from_source(
    source: str,
    evidence: dict[str, Any],
    failures: list[str],
) -> set[str]:
    """Require an evidence tag immediately before each candidate-content construct."""
    known = {
        item.get("id"): item
        for group in ("claims", "projects")
        for item in evidence.get(group, [])
        if isinstance(item, dict) and item.get("id")
    }
    ids_used: set[str] = set()
    pending: list[str] | None = None
    claim_pattern = re.compile(
        r"""(?x)
        ^(?:
          \\newcommand\{\\(?:ResumeSummary|CoreSkills|SelectedProject(?:ID|Title|Context|BulletOne|BulletTwo|BulletThree))\}
          |\\roleheading\b
          |\\clientheading\b
          |\\item\b
          |\{\\LARGE\\bfseries\b
          |Ireland\s+\\textbar
          |\\textbf\{[^{}]+:
        )
        """
    )
    for line_number, line in enumerate(source.splitlines(), start=1):
        evidence_match = re.match(r"^\s*%\s*EVIDENCE:\s*(.*?)\s*$", line)
        if evidence_match:
            pending = [value for value in evidence_match.group(1).split() if value]
            continue
        stripped = line.strip()
        if not stripped:
            continue
        if claim_pattern.search(stripped):
            if not pending:
                failures.append(f"Candidate content on source line {line_number} lacks an EVIDENCE tag")
            else:
                for evidence_id in pending:
                    item = known.get(evidence_id)
                    if item is None:
                        failures.append(
                            f"Unknown source EVIDENCE ID on line {line_number}: {evidence_id}"
                        )
                    elif item.get("status") == "hold":
                        failures.append(
                            f"Held source EVIDENCE ID on line {line_number}: {evidence_id}"
                        )
                    else:
                        ids_used.add(evidence_id)
            pending = None
        elif not stripped.startswith("%"):
            pending = None
    return ids_used


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError:
        pass  # Keep the original macOS fallback for an unconfigured interpreter.
    else:
        try:
            value = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (yaml.YAMLError, OSError) as exc:
            raise RuntimeError(f"Unable to parse {path}: {exc}") from exc
        if not isinstance(value, dict):
            raise RuntimeError(f"Expected a YAML mapping in {path}")
        return value
    ruby = shutil.which("ruby")
    if not ruby:
        raise RuntimeError("Install the workspace requirements (PyYAML), or use Ruby for the fallback YAML parser")
    program = (
        'require "yaml"; require "json"; '
        "value = YAML.safe_load(File.read(ARGV.fetch(0)), aliases: false); "
        "STDOUT.write(JSON.generate(value))"
    )
    result = subprocess.run(
        [ruby, "-e", program, str(path)],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode:
        detail = result.stderr.strip() or "unknown YAML parse error"
        raise RuntimeError(f"Unable to parse {path}: {detail}")
    value = json.loads(result.stdout)
    if not isinstance(value, dict):
        raise RuntimeError(f"Expected a YAML mapping in {path}")
    return value


def inspect_pdf(pdf_path: Path, render_dir: Path) -> dict[str, Any]:
    render_dir.mkdir(parents=True, exist_ok=True)
    for stale_preview in render_dir.glob("page-*.png"):
        stale_preview.unlink()
    swiftc = shutil.which("swiftc")
    swift = shutil.which("swift")
    if (swiftc or swift) and PDF_INSPECTOR.is_file():
        command: list[str]
        if swiftc:
            inspector_hash = sha256(PDF_INSPECTOR)[:12]
            cached_inspector = Path(tempfile.gettempdir()) / f"chetan-pdf-inspect-{inspector_hash}"
            if not cached_inspector.is_file():
                compile_result = subprocess.run(
                    [swiftc, str(PDF_INSPECTOR), "-o", str(cached_inspector)],
                    text=True,
                    capture_output=True,
                    check=False,
                )
                if compile_result.returncode:
                    raise RuntimeError(
                        compile_result.stderr.strip() or "Unable to compile Swift PDF inspector"
                    )
            command = [str(cached_inspector), str(pdf_path), str(render_dir)]
        else:
            command = [str(swift), str(PDF_INSPECTOR), str(pdf_path), str(render_dir)]
        result = subprocess.run(
            command,
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode:
            raise RuntimeError(result.stderr.strip() or "Swift PDF inspection failed")
        return json.loads(result.stdout)

    try:
        from pypdf import PdfReader  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "PDF text inspection requires Swift/PDFKit on macOS or the pypdf package"
        ) from exc

    renderer = shutil.which("pdftoppm")
    if not renderer:
        raise RuntimeError("PDF rendering requires Swift/PDFKit on macOS or Poppler pdftoppm")
    rendered = subprocess.run([renderer, "-png", "-r", "144", str(pdf_path), str(render_dir / "page")], capture_output=True, text=True, timeout=120)
    if rendered.returncode:
        raise RuntimeError(rendered.stderr or "Poppler rendering failed")
    for preview in sorted(render_dir.glob("page-*.png")):
        number = int(preview.stem.split("-")[-1])
        desired = render_dir / f"page-{number:02d}.png"
        if desired != preview:
            preview.rename(desired)

    reader = PdfReader(str(pdf_path))
    pages = []
    for index, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        media_box = page.mediabox
        pages.append(
            {
                "number": index,
                "width_points": float(media_box.width),
                "height_points": float(media_box.height),
                "text_characters": len(text),
                "text": text,
            }
        )
    return {
        "page_count": len(pages),
        "text_characters": sum(page["text_characters"] for page in pages),
        "metadata": {
            "title": str((reader.metadata or {}).get("/Title", "")),
            "author": str((reader.metadata or {}).get("/Author", "")),
            "subject": str((reader.metadata or {}).get("/Subject", "")),
        },
        "pages": pages,
    }


def compile_latex(source_path: Path, output_dir: Path) -> tuple[Path | None, str, str]:
    tectonic = shutil.which("tectonic")
    if not tectonic:
        return None, "", "tectonic is not installed"
    result = subprocess.run(
        [
            tectonic,
            "-p",
            "--keep-logs",
            "--outdir",
            str(output_dir),
            str(source_path),
        ],
        text=True,
        capture_output=True,
        check=False,
        cwd=str(source_path.parent),
    )
    chatter = "\n".join(part for part in (result.stdout, result.stderr) if part)
    pdf_path = output_dir / f"{source_path.stem}.pdf"
    log_path = output_dir / f"{source_path.stem}.log"
    log_text = log_path.read_text(encoding="utf-8", errors="replace") if log_path.is_file() else ""
    if result.returncode or not pdf_path.is_file():
        detail = chatter.strip() or log_text.strip() or f"tectonic exited {result.returncode}"
        return None, log_text, detail
    return pdf_path, log_text, chatter


def add_failure(failures: list[str], condition: bool, message: str) -> None:
    if not condition:
        failures.append(message)


def validate_evidence_map(
    evidence_map_path: Path | None,
    evidence: dict[str, Any],
    selected_project_id: str,
    source_evidence_ids: set[str],
    source_path: Path,
    failures: list[str],
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "required": evidence_map_path is not None,
        "path": str(evidence_map_path) if evidence_map_path else None,
        "sha256": None,
        "job_id": None,
        "role_eligible": None,
        "candidate_revision": None,
        "job_snapshot_sha256": None,
        "supported_requirement_coverage": None,
        "requirements_count": None,
        "company_problem": None,
        "resume_claim_ids": [],
        "source_evidence_ids": sorted(source_evidence_ids),
        "held_claims_used": None,
        "all_candidate_claims_grounded": bool(source_evidence_ids),
    }
    if evidence_map_path is None:
        return result
    if not evidence_map_path.is_file():
        failures.append(f"Missing evidence map: {evidence_map_path}")
        result["all_candidate_claims_grounded"] = False
        return result

    try:
        mapping = load_yaml(evidence_map_path)
    except (RuntimeError, json.JSONDecodeError) as exc:
        failures.append(str(exc))
        result["all_candidate_claims_grounded"] = False
        return result
    result["sha256"] = sha256(evidence_map_path)

    known_claims = {
        item.get("id"): item
        for item in evidence.get("claims", [])
        if isinstance(item, dict) and item.get("id")
    }
    known_projects = {
        item.get("id"): item
        for item in evidence.get("projects", [])
        if isinstance(item, dict) and item.get("id")
    }
    claim_ids = mapping.get("resume_claim_ids")
    held = mapping.get("held_claims_used")
    mapped_project = mapping.get("selected_project_id")
    requirements = mapping.get("requirements")
    company_problem = mapping.get("company_problem")
    coverage = mapping.get("supported_requirement_coverage")
    result.update(
        {
            "job_id": mapping.get("job_id"),
            "role_eligible": mapping.get("role_eligible"),
            "candidate_revision": mapping.get("candidate_revision"),
            "job_snapshot_sha256": mapping.get("job_snapshot_sha256"),
            "supported_requirement_coverage": coverage,
            "requirements_count": len(requirements) if isinstance(requirements, list) else None,
            "company_problem": company_problem,
            "resume_claim_ids": claim_ids if isinstance(claim_ids, list) else [],
            "held_claims_used": held,
        }
    )

    add_failure(
        failures,
        isinstance(mapping.get("job_id"), str) and len(mapping["job_id"].strip()) >= 5,
        "Evidence map needs a stable job_id",
    )
    add_failure(failures, mapping.get("role_eligible") is True, "Evidence map role_eligible must be true")
    add_failure(
        failures,
        mapping.get("candidate_revision") == evidence.get("candidate_revision"),
        "Evidence map candidate_revision does not match context/evidence.yml",
    )

    jd_snapshot = source_path.parent / "job-description.md"
    actual_jd_hash = sha256(jd_snapshot) if jd_snapshot.is_file() else None
    if actual_jd_hash is None:
        failures.append(f"Missing JD snapshot beside tailored resume: {jd_snapshot}")
    add_failure(
        failures,
        isinstance(mapping.get("job_snapshot_sha256"), str)
        and mapping.get("job_snapshot_sha256") == actual_jd_hash,
        "Evidence-map job_snapshot_sha256 does not match the saved JD snapshot",
    )
    add_failure(
        failures,
        mapped_project == selected_project_id,
        "Evidence map selected_project_id does not match LaTeX",
    )
    add_failure(failures, held == [], "held_claims_used must be an empty list")
    add_failure(
        failures,
        isinstance(claim_ids, list) and bool(claim_ids),
        "resume_claim_ids must be a non-empty list",
    )
    add_failure(
        failures,
        isinstance(coverage, (int, float)) and 0 <= float(coverage) <= 100,
        "supported_requirement_coverage must be a number from 0 to 100",
    )

    requirement_ids: set[str] = set()
    if not isinstance(requirements, list) or not requirements:
        failures.append("Evidence map requirements must be a non-empty list")
    else:
        for index, requirement in enumerate(requirements, start=1):
            if not isinstance(requirement, dict):
                failures.append(f"Requirement {index} is not a mapping")
                continue
            requirement_id = requirement.get("id")
            priority = requirement.get("priority")
            text = requirement.get("text")
            mapped_ids = requirement.get("evidence_ids")
            strength = requirement.get("strength")
            if not isinstance(requirement_id, str) or not re.fullmatch(r"R\d{2,}", requirement_id):
                failures.append(f"Requirement {index} has invalid id")
            elif requirement_id in requirement_ids:
                failures.append(f"Duplicate requirement id: {requirement_id}")
            else:
                requirement_ids.add(requirement_id)
            if priority not in {"required", "preferred"}:
                failures.append(f"Requirement {requirement_id or index} has invalid priority")
            if not isinstance(text, str) or len(text.strip()) < 3:
                failures.append(f"Requirement {requirement_id or index} needs text")
            if not isinstance(mapped_ids, list):
                failures.append(f"Requirement {requirement_id or index} needs evidence_ids")
                mapped_ids = []
            if strength not in {"strong", "partial", "gap"}:
                failures.append(f"Requirement {requirement_id or index} has invalid strength")
            if strength in {"strong", "partial"} and not mapped_ids:
                failures.append(
                    f"Requirement {requirement_id or index} claims support without evidence IDs"
                )
            if strength == "gap" and mapped_ids:
                failures.append(f"Gap requirement {requirement_id or index} must not cite evidence")
            for evidence_id in mapped_ids:
                item = known_claims.get(evidence_id) or known_projects.get(evidence_id)
                if not item:
                    failures.append(
                        f"Requirement {requirement_id or index} cites unknown ID: {evidence_id}"
                    )
                elif item.get("status") == "hold":
                    failures.append(
                        f"Requirement {requirement_id or index} cites held ID: {evidence_id}"
                    )

    if not isinstance(company_problem, dict):
        failures.append("Evidence map needs company_problem research")
    else:
        statement = company_problem.get("statement")
        source_url = company_problem.get("source_url")
        research_date = company_problem.get("published_or_accessed")
        evidence_class = company_problem.get("evidence_class")
        confidence = company_problem.get("confidence")
        if not isinstance(statement, str) or len(statement.strip()) < 15:
            failures.append("company_problem.statement is missing or too vague")
        if (
            not isinstance(source_url, str)
            or not re.match(r"^https?://", source_url)
            or "example.invalid" in source_url
        ):
            failures.append("company_problem.source_url must be a real HTTP(S) source")
        try:
            if not isinstance(research_date, str):
                raise ValueError
            datetime.strptime(research_date, "%Y-%m-%d")
        except ValueError:
            failures.append("company_problem.published_or_accessed must be YYYY-MM-DD")
        if evidence_class not in {"explicit", "inferred"}:
            failures.append("company_problem.evidence_class must be explicit or inferred")
        if confidence not in {"high", "medium", "low"}:
            failures.append("company_problem.confidence must be high, medium, or low")

    selected_reason = mapping.get("selected_project_reason")
    add_failure(
        failures,
        isinstance(selected_reason, str)
        and len(selected_reason.strip()) >= 15
        and "replace" not in selected_reason.lower(),
        "selected_project_reason is missing or placeholder text",
    )

    unknown_ids = []
    held_ids = []
    if isinstance(claim_ids, list):
        for claim_id in claim_ids:
            item = known_claims.get(claim_id) or known_projects.get(claim_id)
            if not item:
                unknown_ids.append(str(claim_id))
            elif item.get("status") == "hold":
                held_ids.append(str(claim_id))
    if unknown_ids:
        failures.append(f"Evidence map contains unknown IDs: {', '.join(sorted(unknown_ids))}")
    if held_ids:
        failures.append(f"Evidence map uses held IDs: {', '.join(sorted(held_ids))}")
    declared_ids = set(claim_ids) if isinstance(claim_ids, list) else set()
    if declared_ids != source_evidence_ids:
        missing_from_map = sorted(source_evidence_ids - declared_ids)
        unused_in_source = sorted(declared_ids - source_evidence_ids)
        if missing_from_map:
            failures.append(
                "Evidence map omits source-tagged IDs: " + ", ".join(missing_from_map)
            )
        if unused_in_source:
            failures.append(
                "Evidence map declares IDs not attached to visible source: "
                + ", ".join(unused_in_source)
            )
    if selected_project_id not in declared_ids:
        failures.append("Selected project ID must appear in resume_claim_ids")
    result["all_candidate_claims_grounded"] = (
        bool(claim_ids)
        and not unknown_ids
        and not held_ids
        and held == []
        and declared_ids == source_evidence_ids
    )
    return result


def validate_selected_project(
    source: str,
    evidence: dict[str, Any],
    selected_project_id: str,
    failures: list[str],
) -> dict[str, Any]:
    projects = {
        item.get("id"): item
        for item in evidence.get("projects", [])
        if isinstance(item, dict) and item.get("id")
    }
    project = projects.get(selected_project_id)
    result: dict[str, Any] = {
        "id": selected_project_id or None,
        "title": None,
        "bullet_count": None,
        "content_matches_registry": False,
    }
    if not project:
        return result
    resume_content = project.get("resume_content")
    if not isinstance(resume_content, dict):
        failures.append(f"Selected project has no registered resume_content: {selected_project_id}")
        return result

    macros = extract_zero_argument_macros(strip_latex_comments(source))
    expected_title = str(resume_content.get("title", ""))
    expected_context = str(resume_content.get("context", ""))
    expected_bullets = resume_content.get("bullets")
    if not isinstance(expected_bullets, list) or not 2 <= len(expected_bullets) <= 3:
        failures.append(f"Selected project registry needs 2-3 approved bullets: {selected_project_id}")
        return result

    actual_title = normalize_latex_text(macros.get("SelectedProjectTitle", ""))
    actual_context = normalize_latex_text(macros.get("SelectedProjectContext", ""))
    bullet_names = ("SelectedProjectBulletOne", "SelectedProjectBulletTwo", "SelectedProjectBulletThree")
    actual_bullets = [
        normalize_latex_text(macros.get(name, ""))
        for name in bullet_names[: len(expected_bullets)]
    ]
    expected_bullets_normalized = [normalize_latex_text(str(value)) for value in expected_bullets]
    result["title"] = actual_title
    result["bullet_count"] = len(expected_bullets)

    if actual_title != normalize_latex_text(expected_title):
        failures.append("Selected project title does not match its registered project ID")
    if actual_context != normalize_latex_text(expected_context):
        failures.append("Selected project context does not match its registered project ID")
    if actual_bullets != expected_bullets_normalized:
        failures.append("Selected project bullets do not match the approved project registry")

    start_markers = source.count("% SELECTED_PROJECT_BLOCK_START")
    end_markers = source.count("% SELECTED_PROJECT_BLOCK_END")
    if start_markers != 1 or end_markers != 1:
        failures.append("Selected project block must have exactly one start and end marker")
        return result
    block = source.split("% SELECTED_PROJECT_BLOCK_START", 1)[1].split(
        "% SELECTED_PROJECT_BLOCK_END", 1
    )[0]
    rendered_items = re.findall(
        r"\\item\s+\\(SelectedProjectBullet(?:One|Two|Three))\b",
        strip_latex_comments(block),
    )
    all_item_count = len(re.findall(r"\\item\b", strip_latex_comments(block)))
    expected_names = list(bullet_names[: len(expected_bullets)])
    if rendered_items != expected_names or all_item_count != len(expected_bullets):
        failures.append(
            "Selected project block must render only the registered 2-3 project bullets"
        )
    if len(re.findall(r"\\SelectedProjectTitle\b", block)) != 1:
        failures.append("Selected project title must render exactly once")
    if len(re.findall(r"\\SelectedProjectContext\b", block)) != 1:
        failures.append("Selected project context must render exactly once")
    if re.search(r"\\(?:section|roleheading|clientheading)\b", strip_latex_comments(block)):
        failures.append("Selected project block contains an additional project/section construct")

    result["content_matches_registry"] = not any(
        message.startswith("Selected project") for message in failures
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate Chetan's LaTeX resume and optionally compile a two-page PDF."
    )
    parser.add_argument("tex", type=Path, help="Path to the complete LaTeX resume")
    parser.add_argument("--compile", action="store_true", help="Compile with tectonic and inspect the PDF")
    parser.add_argument("--output", type=Path, help="PDF output path")
    parser.add_argument("--qa-json", type=Path, help="Write the QA manifest as JSON")
    parser.add_argument("--render-dir", type=Path, help="Directory for page preview PNGs")
    parser.add_argument("--evidence-map", type=Path, help="Tailored-resume evidence-map.yml")
    parser.add_argument("--studio-layout", action="store_true", help="Validate ranked Studio typography and measured page fill; all evidence/release gates still apply")
    parser.add_argument(
        "--visual-review",
        choices=("pending", "pass", "fail"),
        default="pending",
        help="Record the human visual-review result",
    )
    parser.add_argument(
        "--visual-reviewer",
        help="Reviewer name/identity; required when --visual-review is pass or fail",
    )
    args = parser.parse_args()

    source_path = args.tex.expanduser().resolve()
    failures: list[str] = []
    warnings: list[str] = []
    qa: dict[str, Any] = {
        "schema_version": 2,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "source": str(source_path),
        "source_sha256": None,
        "candidate_revision": None,
        "selected_project_id": None,
        "project_count": None,
        "compile_ok": False,
        "page_count": None,
        "page2_text_characters": None,
        "pdf_text_extractable": False,
        "required_headings_present": False,
        "overflow_count": None,
        "unresolved_placeholders": [],
        "unsafe_claims": [],
        "visual_review": args.visual_review,
        "visual_reviewer": args.visual_reviewer,
        "visual_reviewed_at": None,
        "preview_sha256": {},
        "release_ready": False,
        "status": "FAIL",
        "failures": failures,
        "warnings": warnings,
    }

    if not source_path.is_file():
        failures.append(f"Missing LaTeX source: {source_path}")
        return finish(args.qa_json, qa, 1)

    try:
        source = source_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        failures.append(f"LaTeX source is not UTF-8: {exc}")
        return finish(args.qa_json, qa, 1)

    qa["source_sha256"] = sha256(source_path)
    clean = strip_latex_comments(source)
    required_order = list(REQUIRED_SECTIONS)
    layout_clean = clean
    if args.studio_layout:
        sys.path.insert(0, str(ROOT))
        from services.resume_layout import validate_density, measure_pages
        layout_errors, layout_clean = validate_density(source)
        failures.extend(layout_errors)
        required_order = re.findall(r"\\section\{([^{}]+)\}", clean)
        allowed_orders = [
            ["Professional Summary", "Core Skills", *middle, "Education", "Technical Skills", "Certifications"]
            for middle in [("Selected Project", "Professional Experience"), ("Professional Experience", "Selected Project")]
        ]
        add_failure(failures, required_order in allowed_orders, "Studio section order must preserve all seven required sections exactly once")

    try:
        evidence = load_yaml(EVIDENCE_PATH)
    except (RuntimeError, json.JSONDecodeError) as exc:
        failures.append(str(exc))
        evidence = {}
    qa["candidate_revision"] = evidence.get("candidate_revision")
    qa["registry_sha256"] = sha256(EVIDENCE_PATH)
    qa["profile_sha256"] = sha256(ROOT / "config/profile.yml")
    profile = load_yaml(ROOT / "config/profile.yml")
    candidate = profile.get("candidate", {})
    phone = candidate.get("phone", "")
    disclosure = profile.get("claim_policy", {}).get("client_name_disclosure", "pending")
    unsafe_patterns = dict(UNSAFE_PATTERNS)
    if not str(disclosure).startswith("approved"):
        unsafe_patterns["client name pending disclosure"] = r"(?i)\b(?:AstraZeneca|NielsenIQ|Hindustan Unilever)\b"
    if candidate.get("phone_external_resume_policy") != "include_exactly_as_supplied":
        unsafe_patterns["unconfirmed phone"] = re.escape(phone or "+353-0892401738")
    source_evidence_ids = evidence_ids_from_source(source, evidence, failures)
    qa["source_evidence_ids"] = sorted(source_evidence_ids)

    add_failure(
        failures,
        len(re.findall(r"\\documentclass\[a4paper," + ("11" if args.studio_layout else "10") + r"pt\]\{article\}", clean)) == 1,
        "Resume must contain exactly one fixed A4 " + ("11pt Studio" if args.studio_layout else "10pt") + " document class",
    )
    geometry_declarations = re.findall(
        r"\\usepackage\[([^\]]*)\]\{geometry\}",
        clean,
    )
    add_failure(
        failures,
        geometry_declarations
        == ["top=0.52in,bottom=0.52in,left=0.62in,right=0.62in"],
        "Resume must contain exactly one fixed geometry declaration",
    )
    line_spread_values = re.findall(
        r"\\renewcommand\{\\baselinestretch\}\{([^{}]+)\}",
        clean,
    )
    add_failure(
        failures,
        line_spread_values == (["1.02"] if args.studio_layout else ["1.04"]),
        "Resume must preserve the single fixed baselinestretch value",
    )
    add_failure(failures, latex_braces_balanced(source), "LaTeX braces are unbalanced")
    add_failure(
        failures,
        clean.rstrip().endswith(r"\end{document}"),
        "Resume must end with \\end{document}",
    )
    add_failure(
        failures,
        clean.count(r"\newpage") == (0 if args.studio_layout else 1),
        "Resume must contain exactly one explicit page break",
    )
    add_failure(
        failures,
        len(
            re.findall(
                r"\\usepackage(?:\[[^\]]*\])?\{hyperref\}",
                clean,
                flags=re.DOTALL,
            )
        )
        == 1,
        "Resume must load hyperref exactly once",
    )

    for label, pattern in PROHIBITED_LAYOUT_PATTERNS.items():
        if re.search(pattern, layout_clean):
            failures.append(f"Prohibited layout detected: {label}")

    placeholder_hits = []
    for label, pattern in PLACEHOLDER_PATTERNS.items():
        if re.search(pattern, clean):
            placeholder_hits.append(label)
            failures.append(f"Unresolved content detected: {label}")
    qa["unresolved_placeholders"] = placeholder_hits

    unsafe_hits = []
    for label, pattern in unsafe_patterns.items():
        if re.search(pattern, clean):
            unsafe_hits.append(label)
            failures.append(f"Unsafe candidate-facing content: {label}")
    qa["unsafe_claims"] = unsafe_hits

    for section in REQUIRED_SECTIONS:
        add_failure(
            failures,
            bool(re.search(rf"\\section\{{{re.escape(section)}\}}", clean)),
            f"Missing required section: {section}",
        )

    add_failure(
        failures,
        len(re.findall(r"\\section\{Selected Project\}", clean)) == 1,
        "Resume must render exactly one Selected Project section",
    )
    add_failure(
        failures,
        not re.search(r"\\section\{(?:Academic )?Projects\}", clean),
        "Resume may not contain an additional Projects section",
    )

    project_matches = re.findall(
        r"\\newcommand\{\\SelectedProjectID\}\{([^{}]+)\}",
        clean,
    )
    selected_project_id = project_matches[0] if len(project_matches) == 1 else ""
    qa["selected_project_id"] = selected_project_id or None
    qa["project_count"] = len(re.findall(r"\\section\{Selected Project\}", clean))
    ready_project_ids = {
        item.get("id")
        for item in evidence.get("projects", [])
        if isinstance(item, dict) and item.get("id")
    }
    add_failure(
        failures,
        len(project_matches) == 1,
        "Resume must declare exactly one SelectedProjectID",
    )
    add_failure(
        failures,
        selected_project_id in ready_project_ids,
        f"Selected project is not resume-ready: {selected_project_id or '<missing>'}",
    )
    project_validation = validate_selected_project(
        source,
        evidence,
        selected_project_id,
        failures,
    )
    qa["selected_project"] = project_validation

    section_positions = []
    for section in required_order:
        match = re.search(rf"\\section\{{{re.escape(section)}\}}", clean)
        section_positions.append(match.start() if match else -1)
    add_failure(
        failures,
        all(
            left < right
            for left, right in zip(section_positions, section_positions[1:])
            if left >= 0 and right >= 0
        ),
        "Required sections are not in the expected ATS reading order",
    )

    required_source_values = (
        "Chetan Babu M",
        "chetanbabu07@gmail.com",
        "linkedin.com/in/chetan-babu",
        "Sep 2023 -- Jan 2025",
        "Feb 2023 -- Aug 2023",
        "Jun 2019 -- May 2023",
        "SRM Institute of Science and Technology",
        "In Progress",
        "pdfauthor={Chetan Babu M}",
    )
    for value in required_source_values:
        add_failure(failures, value in clean, f"Missing required stable content: {value}")

    document_body = clean.split(r"\begin{document}", 1)[-1]
    document_body = expand_zero_argument_macros(clean, document_body)
    page_sources = document_body.split(r"\newpage")
    if len(page_sources) == 2:
        page_word_counts = [approximate_visible_words(page) for page in page_sources]
        qa["source_page_word_counts"] = page_word_counts
        for index, count in enumerate(page_word_counts, start=1):
            if count < 180:
                failures.append(f"Source page {index} is too sparse ({count} approximate words)")
            elif count > 560:
                failures.append(f"Source page {index} is too dense ({count} approximate words)")

    tailored = source_path != BASE_TEMPLATE
    evidence_map_path = args.evidence_map
    if tailored and evidence_map_path is None:
        sibling = source_path.parent / "evidence-map.yml"
        evidence_map_path = sibling
    evidence_map_result = validate_evidence_map(
        evidence_map_path.resolve() if evidence_map_path else None,
        evidence,
        selected_project_id,
        source_evidence_ids,
        source_path,
        failures,
    )
    qa["evidence_map"] = evidence_map_result

    if args.visual_review in {"pass", "fail"}:
        add_failure(
            failures,
            isinstance(args.visual_reviewer, str) and len(args.visual_reviewer.strip()) >= 3,
            "A visual reviewer identity is required for a pass/fail visual review",
        )
        if args.visual_reviewer:
            qa["visual_reviewed_at"] = datetime.now(timezone.utc).isoformat()

    if args.compile:
        with tempfile.TemporaryDirectory(prefix="chetan-resume-build-") as temporary:
            build_dir = Path(temporary)
            pdf_path, log_text, compile_detail = compile_latex(source_path, build_dir)
            if pdf_path is None:
                failures.append(f"LaTeX compilation failed: {compile_detail[-1500:]}")
            else:
                qa["compile_ok"] = True
                overflow_matches = re.findall(r"Overfull \\[hv]box", log_text)
                qa["overflow_count"] = len(overflow_matches)
                if overflow_matches:
                    failures.append(f"LaTeX reported {len(overflow_matches)} overfull box(es)")
                if re.search(r"LaTeX Warning:.*(?:undefined|Rerun)", log_text, re.IGNORECASE):
                    failures.append("LaTeX reported unresolved reference or rerun warnings")

                output_path = (
                    args.output.expanduser().resolve()
                    if args.output
                    else source_path.with_suffix(".pdf")
                )
                render_dir = (
                    args.render_dir.expanduser().resolve()
                    if args.render_dir
                    else output_path.parent / f"{output_path.stem}-preview"
                )
                try:
                    inspection = inspect_pdf(pdf_path, render_dir)
                except (RuntimeError, json.JSONDecodeError) as exc:
                    failures.append(f"PDF inspection failed: {exc}")
                    inspection = {}

                page_count = inspection.get("page_count")
                pages = inspection.get("pages") if isinstance(inspection.get("pages"), list) else []
                all_text = "\n".join(
                    str(page.get("text", "")) for page in pages if isinstance(page, dict)
                )
                qa["page_count"] = page_count
                if args.studio_layout and pages:
                    qa["layout"] = measure_pages(pdf_path, render_dir)
                    add_failure(failures, qa["layout"]["full_two_pages"], "Studio PDF must fill two A4 pages with readable spacing and no large gaps")
                qa["pdf_metadata"] = (
                    inspection.get("metadata")
                    if isinstance(inspection.get("metadata"), dict)
                    else {}
                )
                qa["pdf_text_extractable"] = len(all_text.strip()) >= 1000
                qa["page2_text_characters"] = (
                    pages[1].get("text_characters") if len(pages) >= 2 and isinstance(pages[1], dict) else None
                )
                qa["render_dir"] = str(render_dir)
                add_failure(failures, page_count == 2, f"Compiled PDF must have exactly 2 pages; found {page_count}")
                add_failure(
                    failures,
                    qa["pdf_text_extractable"],
                    "Compiled PDF text is missing or not sufficiently extractable",
                )
                add_failure(
                    failures,
                    qa["pdf_metadata"].get("author") == "Chetan Babu M"
                    and str(qa["pdf_metadata"].get("title", "")).startswith("Chetan Babu M"),
                    "Compiled PDF metadata author/title does not match Chetan",
                )

                for page in pages:
                    if not isinstance(page, dict):
                        continue
                    width = float(page.get("width_points", 0))
                    height = float(page.get("height_points", 0))
                    add_failure(
                        failures,
                        abs(width - 595.3) <= 3 and abs(height - 841.9) <= 3,
                        f"PDF page {page.get('number')} is not A4 ({width:.1f} x {height:.1f} pt)",
                    )
                    add_failure(
                        failures,
                        int(page.get("text_characters", 0)) >= 900,
                        f"PDF page {page.get('number')} is suspiciously sparse",
                    )

                missing_pdf_headings = [
                    heading for heading in REQUIRED_SECTIONS if heading not in all_text
                ]
                qa["required_headings_present"] = not missing_pdf_headings
                if missing_pdf_headings:
                    failures.append(
                        "PDF text is missing headings: " + ", ".join(missing_pdf_headings)
                    )
                if re.search(
                    r"\b(?:IDENTITY|CONTACT|EXP|EDU|CERT|PROJ|WORK|TRAINING|COURSEWORK|SKILL|LANG|HOLD)-[A-Z0-9-]+\b",
                    all_text,
                ):
                    failures.append("Evidence IDs leaked into visible PDF text")
                for label, pattern in unsafe_patterns.items():
                    if re.search(pattern, all_text):
                        failures.append(f"Unsafe content appears in compiled PDF: {label}")

                preview_files = sorted(path.name for path in render_dir.glob("page-*.png"))
                expected_preview_files = ["page-01.png", "page-02.png"]
                add_failure(
                    failures,
                    preview_files == expected_preview_files,
                    "Preview directory must contain exactly page-01.png and page-02.png",
                )
                qa["preview_sha256"] = {
                    filename: sha256(render_dir / filename)
                    for filename in expected_preview_files
                    if (render_dir / filename).is_file()
                }

                normalized_pdf_text = (
                    all_text.replace("\u2013", "-")
                    .replace("\u2014", "-")
                    .replace("\u2212", "-")
                    .replace("\u00a0", " ")
                )
                first_page_text = (
                    str(pages[0].get("text", "")) if pages and isinstance(pages[0], dict) else ""
                )
                expected_header = (
                    "Chetan Babu M\n"
                    "Ireland | chetanbabu07@gmail.com | linkedin.com/in/chetan-babu"
                )
                add_failure(
                    failures,
                    first_page_text.startswith(expected_header) and (not phone or phone in first_page_text),
                    "Visible PDF header identity/contact does not match the canonical profile",
                )
                visible_invariants = (
                    "Infocepts Technologies Pvt. Ltd.",
                    "Sep 2023 - Jan 2025",
                    "Feb 2023 - Aug 2023",
                    "Munster Technological University",
                    "Sep 2025 - Sep 2026",
                    "MSc programme in Data Science - In Progress",
                    "SRM Institute of Science and Technology",
                    "Jun 2019 - May 2023",
                    "Bachelor of Technology - Computer Science (AI and ML), CGPA: 9.4/10",
                )
                for value in visible_invariants:
                    add_failure(
                        failures,
                        value in normalized_pdf_text,
                        f"Compiled PDF is missing visible invariant: {value}",
                    )

                expected_project_title = project_validation.get("title")
                add_failure(
                    failures,
                    isinstance(expected_project_title, str)
                    and (sum(line.strip() == expected_project_title for line in normalized_pdf_text.splitlines()) == 1 if args.studio_layout else normalized_pdf_text.count(expected_project_title) == 1),
                    "Compiled PDF must show the registered selected-project title exactly once",
                )
                heading_positions = [normalized_pdf_text.find(heading) for heading in required_order]
                qa["text_order_ok"] = all(
                    left >= 0 and right >= 0 and left < right
                    for left, right in zip(heading_positions, heading_positions[1:])
                )
                add_failure(
                    failures,
                    qa["text_order_ok"],
                    "Compiled PDF headings are not in the expected ATS reading order",
                )

                numeric_text = re.sub(
                    r"\b\S+@\S+\b|linkedin\.com/\S+",
                    "",
                    normalized_pdf_text.replace(phone, "") if phone else normalized_pdf_text,
                    flags=re.IGNORECASE,
                )
                visible_numbers = set(
                    re.findall(r"(?<![A-Za-z0-9])\d+(?:,\d{3})*(?:\.\d+)?", numeric_text)
                )
                unsupported_numbers = sorted(visible_numbers - ALLOWED_VISIBLE_NUMBERS)
                qa["visible_numbers"] = sorted(visible_numbers)
                if unsupported_numbers:
                    failures.append(
                        "Compiled PDF contains unregistered numeric claims/values: "
                        + ", ".join(unsupported_numbers)
                    )

                qa["compiled_pdf_sha256"] = sha256(pdf_path)
                qa["pdf"] = str(output_path)
                qa["published_pdf"] = False
                if not failures and args.visual_review != "fail":
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(pdf_path, output_path)
                    qa["published_pdf"] = True
                    qa["pdf_sha256"] = sha256(output_path)
                    add_failure(
                        failures,
                        output_path.stat().st_mtime >= source_path.stat().st_mtime,
                        "Compiled PDF is older than its LaTeX source",
                    )
    else:
        warnings.append("Compilation and PDF gates were skipped")

    if args.visual_review == "fail":
        failures.append("Manual visual review failed")
    elif args.visual_review == "pending":
        warnings.append("Manual visual review is pending; artifact is not release-ready")

    qa["release_ready"] = (
        not failures
        and args.compile
        and args.visual_review == "pass"
        and bool(args.visual_reviewer)
        and qa["compile_ok"]
        and qa["page_count"] == 2
        and qa.get("published_pdf") is True
        and qa.get("selected_project", {}).get("content_matches_registry") is True
        and qa.get("evidence_map", {}).get("all_candidate_claims_grounded") is True
        and set(qa.get("preview_sha256", {})) == {"page-01.png", "page-02.png"}
    )
    if failures:
        qa["status"] = "FAIL"
        exit_code = 1
    elif qa["release_ready"]:
        qa["status"] = "PASS"
        exit_code = 0
    else:
        qa["status"] = "AUTOMATED_PASS_MANUAL_PENDING"
        exit_code = 0
    return finish(args.qa_json, qa, exit_code)


def finish(qa_json_path: Path | None, qa: dict[str, Any], exit_code: int) -> int:
    if qa_json_path:
        path = qa_json_path.expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(qa, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    for warning in qa.get("warnings", []):
        print(f"WARN: {warning}")
    for failure in qa.get("failures", []):
        print(f"FAIL: {failure}")
    print(
        f"{qa.get('status')}: project={qa.get('selected_project_id')} "
        f"pages={qa.get('page_count')} release_ready={qa.get('release_ready')}"
    )
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
