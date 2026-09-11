#!/usr/bin/env python3
"""Verify shared tracking, preserved pack locations and the cleaned layout."""
import hashlib
import json
import sys
from pathlib import Path
from career import Workspace

ROOT = Path(__file__).resolve().parents[2]


def main():
    failures = []
    for name in ["daily-job-search", "career-dashboard", "backup"]:
        if not (ROOT / name).is_dir():
            failures.append(f"Missing {name}")
    for name in [
        "example",
        "resume-builder-main",
        "2026-08-12",
        "Arup-Data-Scientist-Work-Placement",
        "_runtime",
        "_backups",
    ]:
        folder = ROOT / name
        if (
            name == "resume-builder-main"
            and folder.is_dir()
            and all(
                p.suffix == ".code-workspace" for p in folder.rglob("*") if p.is_file()
            )
        ):
            continue
        if folder.exists():
            failures.append(f"Retired folder remains active: {name}")
    w = Workspace(ROOT / "career-dashboard")
    with w.connect() as db:
        if db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            failures.append("Database integrity check failed")
        if list(db.execute("PRAGMA foreign_key_check")):
            failures.append("Broken database relationships")
    historical = json.loads((w.root / "data/historical-packs.json").read_text())
    for item in historical:
        source = ROOT / item["folder"] / "resume.tex"
        if (
            not source.exists()
            or hashlib.sha256(source.read_bytes()).hexdigest() != item["source_sha256"]
        ):
            failures.append("Historical source missing or changed: " + item["folder"])
    for job in w.jobs():
        if job["folder"] and not (w.root / job["folder"]).is_dir():
            failures.append("Missing draft: " + job["id"])
    for run in w.search_runs():
        target = ROOT / "daily-job-search" / run["date"] / "run.json"
        if not target.exists() or json.loads(target.read_text()) != run:
            failures.append("Stale search projection: " + run["date"])
    for name, expected in [
        ("jobs.json", w.jobs()),
        ("activity.json", w.activity(limit=-1)),
    ]:
        target = w.root / "data" / name
        if not target.exists() or json.loads(target.read_text()) != expected:
            failures.append("Stale tracking projection: " + name)
    print(
        json.dumps(
            {
                "status": "FAIL" if failures else "PASS",
                "historical_packs": len(historical),
                "jobs": len(w.jobs()),
                "runs": len(w.search_runs()),
                "failures": failures,
            },
            indent=2,
        )
    )
    return bool(failures)


if __name__ == "__main__":
    sys.exit(main())
