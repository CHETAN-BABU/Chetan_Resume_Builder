# Mode: Batch Resumes — Up to Ten Isolated Tailored Artifacts

Use when Chetan supplies multiple verified JDs/URLs, asks for the top eligible
jobs in the verified pipeline, or says "give me 10 companies". Maximum released
batch size: 10.

## Ten-company trigger

Unless Chetan explicitly requests a list only, "give me 10 companies" means:

`discover -> verify 10 eligible live JDs -> rank -> build 10 full resumes -> compile -> visual QA -> deliver PDFs`

Rejected, duplicate, expired, inaccessible, and out-of-scope leads do not count
toward the requested ten. Continue searching replacements across all approved
role tracks and Ireland locations. If the honest search is exhausted below ten,
release the valid subset and document the search coverage and exact shortage.

## Preflight

1. Create a stable run ID: `{YYYYMMDD-HHMM}-{short-hash}`.
2. When JDs were not supplied, discover and verify the requested number before
   finalising the release manifest.
3. Save a durable manifest at `output/batches/{run-id}/batch.yml`; keep its input identity/hash fields immutable while the runner replaces status atomically.
4. For each input, save a JD snapshot and SHA-256 hash.
5. Verify role, location, seniority, liveness, and application route.
6. Reject duplicates and ineligible jobs before resume generation; search for
   replacements when discovery is part of the request.

A request for “10 resumes” does not authorize creating generic company documents without ten usable JDs.

## Per-job isolation

Use a unique directory:

```text
output/batches/{run-id}/{index}-{company-slug}-{role-slug}-{job-hash}/
  job-description.md
  evaluation.md
  company-research.md
  evidence-map.yml
  resume.tex
  resume.pdf
  resume-preview/
    page-01.png
    page-02.png
  qa.json
```

Do not reuse company research, requirement IDs, content plans, or selected projects across workers unless each job independently supports them.

The batch runner also owns `worker.log` as an operational audit file. It is required for a batch worker but is not one of the nine per-job release artifacts.

## Worker contract

Each job follows:

`snapshot -> eligibility -> evaluation -> research -> evidence map -> two projects -> write -> compile -> QA -> visual review`

A worker is complete only when all nine required artifact paths exist and `qa.json` reports every hard gate as passed. An exit code alone is not completion.

Use at most three evidence-safe render repairs. Preserve the failed artifacts and failure reason; never hide a failure by manufacturing content.

## State and resumability

Track:

| Field | Meaning |
|---|---|
| job_id | Stable per-JD hash |
| status | pending / running / passed / rejected / failed |
| attempts | Render/QA attempts |
| selected_project_id | Exactly one when passed |
| page_count | Must be 2 when passed |
| coverage | Diagnostic supported requirement coverage |
| error | Exact last failure |

Resume a run by skipping only `passed` and policy-`rejected` items whose snapshots and candidate revision have not changed.

Use `scripts/run_resume_batch.py` when workers are executable commands. Define `worker_command` as a shell-free YAML argument list at manifest or job level; placeholders include `{job_id}`, `{artifact_dir}`, `{snapshot_path}`, and `{attempt}`. The runner alone writes manifest status. A worker may write `worker-result.json` with `{"status":"rejected","reason":"..."}`; otherwise completion is determined from the nine artifacts and a fresh release audit.

`python3 scripts/run_resume_batch.py output/batches/{run-id}/batch.yml --retry-limit 3`

## Cross-batch audit

After all workers finish:

1. Compare name, email, LinkedIn, employer titles/dates, education status/dates, metrics, and ownership wording across every resume.
2. Confirm ten unique output paths and matching JD hashes.
3. Confirm every passed resume has exactly two selected projects and two pages.
4. Flag near-identical summaries or bullet ordering; tailoring should reflect real differences in requirements.
5. Report passed, rejected, failed, and retryable counts.

Run the machine gate:

`python3 scripts/validate_batch.py output/batches/{run-id}/batch.yml --json output/batches/{run-id}/batch-qa.json`

The batch succeeds only with truthful artifacts. When discovery is part of a
ten-company request, first try to replace rejected leads so the release count
can still reach ten. If only eight eligible live roles can be verified after a
documented broad search, eight valid resumes plus an explicit two-role shortage
is correct; fabricating two more is not.
