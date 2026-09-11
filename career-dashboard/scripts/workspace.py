#!/usr/bin/env python3
"""Shared chat interface for the React dashboard's SQLite state."""
import argparse, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]
from career import Workspace
from services.workspace_v2 import CareerServices
from services.agents import AgentRunner


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=[
            "summary",
            "goals",
            "profile",
            "mail",
            "runs",
            "export",
            "save-profile",
            "remove-profile",
            "confirm-mail",
            "run",
        ],
    )
    parser.add_argument("--file", type=Path)
    parser.add_argument("--id")
    parser.add_argument("--job-id")
    parser.add_argument("--kind", choices=["research", "email", "discovery"])
    args = parser.parse_args()
    s = CareerServices(Workspace(ROOT))
    if args.command == "save-profile":
        if not args.file:
            parser.error("--file is required")
        result = s.save_knowledge(json.loads(args.file.read_text()), args.id)
    elif args.command == "remove-profile":
        result = s.delete_knowledge(args.id)
    elif args.command == "confirm-mail":
        result = s.resolve_mail(args.id, args.job_id)
    elif args.command == "run":
        if not args.kind:
            parser.error("--kind is required")
        runner = AgentRunner(s)
        result = runner.enqueue(args.kind, args.job_id)
        print(json.dumps(result), flush=True)
        runner.pool.shutdown(wait=True)
        result = s.runs()[0]
    elif args.command == "profile":
        result = s.knowledge()
    elif args.command == "export":
        s.export_profile()
        s.w.export_tracking()
        s.export_state()
        result = {"exported": True}
    else:
        result = getattr(s, args.command)()
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
