---
description: "Resumable isolated generation and QA for 2-10 verified Chetan jobs; a 10-company request includes discovery and 10 complete resumes."
---

# Generate Resume Batch

1. Read `AGENTS.md` and `workflows/modes/batch-resumes.md`.
2. If Chetan says "give me 10 companies", run job discovery first and continue
   through rejected/expired/duplicate leads until 10 distinct eligible live JDs
   are secured or the documented search is exhausted.
3. Preflight 2–10 release JDs or verified URLs.
4. Save a batch manifest, unique job IDs, snapshots, and hashes.
5. Run `workflows/generate-tailored-resume.md` independently per job.
6. Require the canonical nine per-job release artifact paths: `job-description.md`, `evaluation.md`, `company-research.md`, `evidence-map.yml`, `resume.tex`, `resume.pdf`, `resume-preview/page-01.png`, `resume-preview/page-02.png`, and `qa.json`.
7. Treat missing artifacts or failed QA as worker failure even when compilation exits successfully.
8. Resume safely by skipping only passed jobs whose JD hash and candidate revision have not changed.
9. Run the cross-batch invariant audit.
10. Return a ranked company/role table plus passed, rejected, failed, and
    retryable jobs with direct PDF and artifact-folder paths.

Search for honest replacement roles when discovery is in scope. If fewer than
the requested count remain after broad verification, report the shortage; do
not fabricate replacement resumes.
