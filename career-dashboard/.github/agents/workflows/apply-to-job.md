---
description: "Evaluate an Ireland role and prepare truthful application materials for Chetan after it passes the profile gate."
---

# Apply-to-Job Preparation

This workflow prepares materials. It does not submit an application.

## 1. Verify and classify

- Confirm the specific job page is active.
- Classify as Analytics, BI Delivery, Applied Data Science — Emerging, or Excluded.
- Stop for AI/ML/GenAI roles requiring professional production engineering, software/full-stack, MLOps/DevOps, hardware, or production Data Engineering. Entry-level retrieval-application roles may continue only when project evidence is accepted.
- Create an isolated `output/applications/{job-id}/` folder and save the full verified posting as `job-description.md`.

## 2. Evaluate

Run `workflows/modes/evaluate.md` and calculate the score from `workflows/modes/_shared.md`.

- 70+: proceed with tailoring
- 55–69: proceed only when gaps are manageable and explicitly shown
- Below 55 or excluded: recommend skipping

Save the complete eligibility, job-fit, requirements, evidence mapping, coverage, gaps, and tailoring plan as `output/applications/{job-id}/evaluation.md`.

## 3. Research

For every role that proceeds to tailoring, run `workflows/modes/deep.md` and save current, cited research to `output/applications/{job-id}/company-research.md`.

## 4. Tailor the resume

Run `@resume-builder` using:

- canonical Chetan profile files
- the full job description
- verified company research
- the base `templates/resume-base.tex`

Save the evidence sidecar to `output/applications/{job-id}/evidence-map.yml` and the complete tailored source to `output/applications/{job-id}/resume.tex`.

## 5. Validate

- Run `python3 scripts/validate_workspace.py`.
- Compile and validate with:
  `python3 scripts/validate_resume.py output/applications/{job-id}/resume.tex --compile --output output/applications/{job-id}/resume.pdf --render-dir output/applications/{job-id}/resume-preview --qa-json output/applications/{job-id}/qa.json`
- Inspect `resume-preview/page-01.png` and `resume-preview/page-02.png`, then record the visual review through the validator.
- Confirm every candidate claim has supporting evidence.
- Release only when all nine required paths exist: `job-description.md`, `evaluation.md`, `company-research.md`, `evidence-map.yml`, `resume.tex`, `resume.pdf`, `resume-preview/page-01.png`, `resume-preview/page-02.png`, and `qa.json`.

## 6. Optional outreach

Draft outreach using `workflows/linkedin-outreach.md`. Do not send it without explicit authorization.

## 7. Track

After the user applies, update:

- `data/application-tracker.md`
- `data/applied-companies.md`

Record actual dates and outcomes; do not auto-mark silence as rejection.


Current tracking contract: `data/career.db` is authoritative. `data/pipeline.md`, `data/application-tracker.md` and `data/applied-companies.md` are generated projections; do not edit them directly. Read live records with `python3 scripts/career.py jobs`, add via `add --file <job.json>`, and record user-reported status via `update`. Preparing a PDF never establishes an application.
