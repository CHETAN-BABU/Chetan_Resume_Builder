# Mode: Scan — Ireland Job Discovery

Discover current Ireland-based roles that pass Chetan's role and evidence guardrails.

## Inputs

- `AGENTS.md`
- `config/profile.yml`
- `config/portals.yml`
- `data/pipeline.md`
- `data/application-tracker.md`
- `data/applied-companies.md`

## Process

For a requested count, keep scanning after exclusions, duplicates, expired
postings, and inaccessible pages until the number of verified eligible jobs is
reached or the documented search is exhausted.

### 1. Scan direct career pages

For each enabled company in `config/portals.yml`:

1. Open the career page.
2. Filter for analytics, BI/reporting, and eligible junior data-science titles.
3. Open each specific job page.
4. Capture title, company, location, URL, posting date if shown, and summary of duties.

### 2. Run configured discovery queries

Use the enabled `search_queries` in `config/portals.yml`. Search results are leads only; open and validate the specific employer/ATS job page before inclusion.

### 3. Apply the role gate

Reject:

- AI/Generative AI/ML roles requiring professional production engineering
- Software, full-stack, DevOps, MLOps, hardware, or embedded roles
- Production-pipeline/platform Data Engineer roles
- Senior/lead/principal/manager/director roles requiring unsupported tenure
- Generic “data” roles whose duties are not analytics, BI, reporting, or entry-level data science

For Data Scientist roles, confirm that the seniority and requirements accept academic/graduate evidence. For entry-level GenAI application roles, confirm that candidate projects are accepted and that production-platform ownership is not required.

### 4. Validate liveness

The specific job page must show the role, company, Ireland location, job description, and an active application route. Generic portal pages remain `NEEDS_MANUAL_CHECK`.

### 5. Deduplicate

Check:

1. `data/scan-history.tsv`
2. `data/pipeline.md`
3. `data/application-tracker.md`
4. `data/applied-companies.md`

Do not use retired Version1/Version2 lists for candidate matching.

## Output

Record verified and eligible jobs through `scripts/career.py add --file <job.json>` or the dashboard; `data/pipeline.md` is a generated read-only projection:

```text
- [ ] {url} | {company} | {title} | {track} | {location}
```

Log each reviewed URL to `data/scan-history.tsv`:

```text
{url}\t{date}\t{source}\t{title}\t{company}\t{track}\t{status}
```

Report counts for scanned, eligible, excluded by role, expired/broken, duplicate, needs manual check, and newly queued.


Current tracking contract: `data/career.db` is authoritative. `data/pipeline.md`, `data/application-tracker.md` and `data/applied-companies.md` are generated projections; do not edit them directly. Read live records with `python3 scripts/career.py jobs`, add via `add --file <job.json>`, and record user-reported status via `update`. Preparing a PDF never establishes an application.
