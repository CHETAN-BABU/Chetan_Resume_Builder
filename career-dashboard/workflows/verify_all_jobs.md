---
description: Verify URLs in Chetan's active Ireland job pipeline and tracker without treating generic career portals as active postings.
---

# Verify Active Job URLs

## Scope

Verify only current working files:

- `data/pipeline.md`
- `data/application-tracker.md`

Retired Version1/Version2 lists are not active inputs.

## 1. Run the URL skill

Use `.agents/skills/verify-job-url/`:

```bash
python3 .agents/skills/verify-job-url/scripts/verify_job_url.py \
  --file data/pipeline.md \
  --delay 8 \
  --output data/verification-results.json
```

If the tracker contains direct URLs, run it separately.

## 2. Manual verification

For each result:

- `ACTIVE`: still open the page and confirm the specific title, company, Ireland location, description, and application route.
- `NEEDS_MANUAL_CHECK`: search the portal for the exact role.
- `EXPIRED` or `BROKEN`: confirm once in a browser before changing the tracker.

## 3. Re-check role eligibility

An active URL is not necessarily suitable. Apply the exclusions in `config/profile.yml`, especially AI/ML/GenAI roles requiring professional production engineering and software/MLOps roles.

## 4. Update

- Move confirmed expired or broken entries out of the active pipeline.
- Preserve application history in the tracker; mark status rather than deleting applied records.
- Record the verification date and evidence.
- Never submit an application.


Current tracking contract: `data/career.db` is authoritative. `data/pipeline.md`, `data/application-tracker.md` and `data/applied-companies.md` are generated projections; do not edit them directly. Read live records with `python3 scripts/career.py jobs`, add via `add --file <job.json>`, and record user-reported status via `update`. Preparing a PDF never establishes an application.
