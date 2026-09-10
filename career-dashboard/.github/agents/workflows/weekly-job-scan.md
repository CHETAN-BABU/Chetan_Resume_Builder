---
description: "Weekly scan for verified Ireland analytics, BI, reporting, Power BI, and suitable junior data-science roles for Chetan."
---

# Weekly Ireland Job Scan

## 1. Load profile and history

Read:

- `AGENTS.md`
- `config/profile.yml`
- `config/portals.yml`
- `data/pipeline.md`
- `data/application-tracker.md`
- `data/applied-companies.md`

## 2. Discover

1. Scan enabled company career pages.
2. Run enabled search queries.
3. Focus on Data Analyst, BI Analyst, BI/Power BI Developer, Reporting/Insights Analyst, and junior/graduate Data Scientist roles.

## 3. Exclude

Reject AI/GenAI/ML roles requiring professional production engineering, Software/Full-Stack, DevOps/MLOps, hardware/embedded, and pipeline-platform Data Engineer roles. Entry-level retrieval-application roles require explicit acceptance of candidate projects. Reject unsupported seniority.

## 4. Validate

Open the specific job page and confirm title, company, Ireland location, description, date when shown, and active application route. Flag generic portals for manual review.

## 5. Rank

Use the score in `workflows/modes/_shared.md` only after eligibility passes. Show evidence type and gaps, especially for data-science roles.

## 6. Update

Record verified, deduplicated leads with `scripts/career.py add --file <job.json>`; `data/pipeline.md` is a read-only projection. Do not apply, send outreach, or alter applied-job status without authorization.

Report:

- employers/pages scanned
- eligible roles
- excluded role mismatches
- expired/broken pages
- duplicates
- manual checks
- new queued roles


Current tracking contract: `data/career.db` is authoritative. `data/pipeline.md`, `data/application-tracker.md` and `data/applied-companies.md` are generated projections; do not edit them directly. Read live records with `python3 scripts/career.py jobs`, add via `add --file <job.json>`, and record user-reported status via `update`. Preparing a PDF never establishes an application.
