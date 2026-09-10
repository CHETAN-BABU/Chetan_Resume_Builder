---
description: "Refresh Chetan's current Ireland job pipeline and tracker, removing expired leads and excluding profile-mismatched roles."
---

# Refresh Ireland Job Data

## Active files

- `data/pipeline.md`
- `data/scan-history.tsv`
- `data/application-tracker.md`
- `data/applied-companies.md`

Do not refresh or republish retired Version1/Version2 lists.

## Steps

1. Read `AGENTS.md`, `config/profile.yml`, and `workflows/modes/_shared.md`.
2. Verify every pending URL using the `verify-job-url` skill and a manual browser check.
3. Mark expired, broken, redirected, or generic-portal links accurately.
4. Re-run the role gate; remove mismatched AI/ML/software/MLOps leads from the pending pipeline.
5. Preserve applied-job history in the tracker even when a posting closes.
6. Scan configured portals and searches for new eligible Ireland roles.
7. Add only specific, verified job pages and deduplicate before writing.
8. Update timestamps and report checked, active, expired, mismatched, duplicate, and newly queued counts.


Current tracking contract: `data/career.db` is authoritative. `data/pipeline.md`, `data/application-tracker.md` and `data/applied-companies.md` are generated projections; do not edit them directly. Read live records with `python3 scripts/career.py jobs`, add via `add --file <job.json>`, and record user-reported status via `update`. Preparing a PDF never establishes an application.
