---
description: "End-to-end single-job workflow: verify, evaluate, research, select one real project, compile exactly two pages, and release only after QA."
---

# Generate Tailored Resume

1. Read `AGENTS.md`, the canonical profile/evidence files, and both detailed
   project sources (`context/sources/masters-projects.md` and
   `context/sources/portfolio-audit.md`). Visible claims must still map to the registry.
2. Save and hash the full JD as `output/applications/{job-id}/job-description.md`.
3. Run `workflows/modes/evaluate.md`, save `output/applications/{job-id}/evaluation.md`, and stop excluded roles.
4. Run `workflows/modes/deep.md`; save sourced company-problem research.
5. Run `workflows/modes/resume.md`; write the evidence map before LaTeX.
6. Select exactly one resume-ready project from `context/evidence.yml`.
7. Compile and validate with `scripts/validate_resume.py`.
8. Repair evidence-safe content at most three times.
9. Run `workflows/modes/quality.md`, including both-page visual review.
10. Return all nine required paths—`job-description.md`, `evaluation.md`, `company-research.md`, `evidence-map.yml`, `resume.tex`, `resume.pdf`, `resume-preview/page-01.png`, `resume-preview/page-02.png`, and `qa.json`—plus separate job-fit, supported-coverage, and QA results.

Do not submit an application or send outreach without explicit authorization.
