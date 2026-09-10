#!/usr/bin/env python3
"""Manage daily searches using the dashboard's single application database."""
import argparse
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'career-dashboard/scripts'))
from career import Workspace, job_url
from tracking import today


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('list')
    start = sub.add_parser('start'); start.add_argument('--date', default=today())
    add = sub.add_parser('add'); add.add_argument('--date', default=today())
    add.add_argument('--file', type=Path, required=True)
    link = sub.add_parser('link'); link.add_argument('job_id'); link.add_argument('--date', default=today())
    notes = sub.add_parser('notes'); notes.add_argument('--date', default=today()); notes.add_argument('--file', type=Path, required=True)
    args = parser.parse_args(); workspace = Workspace(ROOT/'career-dashboard')
    if args.command == 'list': result = workspace.search_runs()
    elif args.command == 'start': result = workspace.start_search(args.date)
    elif args.command == 'link': result = workspace.track_search_job(args.job_id, args.date)
    elif args.command == 'notes': result = workspace.update_search(args.date, args.file.read_text())
    else:
        workspace.start_search(args.date)  # Validate the run date before saving a posting.
        values = json.loads(args.file.read_text())
        existing = next((j for j in workspace.jobs() if j['url'] == job_url(values['url'])), None)
        job = existing or workspace.add_job(**values)
        result = workspace.track_search_job(job['id'], args.date)
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == '__main__': main()
