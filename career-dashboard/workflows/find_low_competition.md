---
description: Find lower-competition Ireland opportunities that truthfully match Chetan's analytics, BI, and emerging data-science profile.
---

# Find Lower-Competition Opportunities

## 1. Load exclusions and history

Read:

- `AGENTS.md`
- `config/profile.yml`
- `data/applied-companies.md`
- `data/application-tracker.md`
- `data/pipeline.md`

## 2. Search eligible roles

Prioritize:

- Data/BI/reporting roles in pharmaceutical, FMCG, healthcare, insurance, finance, manufacturing, and operations teams
- Power BI or specialist BI roles where Chetan's PL-300 and enterprise delivery are relevant
- Mid-sized organizations and roles posted recently
- Junior/graduate Data Scientist roles that accept academic projects

Reject AI/ML/GenAI roles requiring professional production engineering, Software Engineer, MLOps, hardware, and pipeline-platform Data Engineer roles.

## 3. Validate and score

For every lead:

1. Open the specific job page.
2. Confirm title, company, Ireland location, description, and application route.
3. Run the role gate in `workflows/modes/_shared.md`.
4. Assess required years and hard requirements.
5. Record applicant count only when visible; do not estimate it as fact.
6. Deduplicate against the current pipeline, tracker, and applied-company list.
7. Score with `workflows/modes/_shared.md`.

When a requested count is supplied, excluded, expired, inaccessible, and
duplicate leads do not consume that count; keep searching for replacements.

## 4. Report

```markdown
# Lower-Competition Opportunities — YYYY-MM-DD

| Company | Role | Track | Posting age | Applicant evidence | Fit | Priority |
|---------|------|-------|-------------|--------------------|-----|----------|
```

Explain why each role fits using only Chetan's canonical evidence. Add verified roles to `data/pipeline.md` only when the active workflow authorizes that write.


Current tracking contract: `data/career.db` is authoritative. `data/pipeline.md`, `data/application-tracker.md` and `data/applied-companies.md` are generated projections; do not edit them directly. Read live records with `python3 scripts/career.py jobs`, add via `add --file <job.json>`, and record user-reported status via `update`. Preparing a PDF never establishes an application.
