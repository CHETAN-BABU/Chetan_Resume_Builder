# Shared System Rules

## Sources of truth

Read in this order:

1. `AGENTS.md`
2. `config/profile.yml`
3. `context/evidence.yml`
4. `context/sources/career.md`
5. `context/sources/masters-projects.md`
6. `context/sources/portfolio-audit.md`
7. `context/PROFILE-NOTES.md`
8. `context/PROFILE.md`
9. `workflows/modes/_profile.md`
10. `templates/resume-base.tex` as a rendering template when generating a resume
11. `config/portals.yml` when discovering jobs

`../backup/previous-backups/` is reference-only. Retired Version1/Version2 job files are not profile or active-job sources.

The LaTeX template is not candidate evidence. Every candidate-facing claim must map to stable IDs in `context/evidence.yml`; put those IDs in a sidecar evidence map, not in visible resume text.
The detailed project Markdown files support the registry but never override its
approved external wording inside a resume.

## Mandatory role gate

Classify every job before scoring or tailoring:

| Track | Eligible titles |
|------|-----------------|
| **Analytics** | Data Analyst, BI Analyst, Business Intelligence Analyst, Insights Analyst, Analytics Analyst |
| **BI Delivery** | BI Developer, Power BI Developer, Reporting Analyst |
| **Applied Data Science — Emerging** | Junior Data Scientist, Graduate Data Scientist, entry-level Data Scientist accepting academic work |
| **GenAI Applications — Project Track** | Entry-level application roles accepting a retrieval project instead of professional production experience |

Reject AI/GenAI/ML roles requiring professional production engineering, software/full-stack, DevOps/MLOps, hardware/embedded, and production-pipeline Data Engineer roles. A job is not eligible merely because its title contains “data,” “analytics,” or “engineer.”

## Job priority score

Only score jobs that pass the role gate.

| Dimension | Weight | Question |
|-----------|--------|----------|
| **Skill and responsibility match** | 40% | Do the actual duties match Chetan's supported professional or academic evidence? |
| **Seniority/evidence fit** | 25% | Does the role accept 3+ years combined professional/internship experience, with the additional internship chronology still unspecified or graduate-level evidence? |
| **Location and work requirements** | 15% | Is it Ireland-based and compatible with the current, verified status? |
| **Posting quality and liveness** | 10% | Is there a specific, current job page with an application route? |
| **Competition** | 10% | Is the role reasonably targeted rather than a broad, highly saturated mismatch? |

### Recommendation bands

- 85–100: strong match; apply promptly
- 70–84: good match; tailor carefully
- 55–69: conditional; proceed only with manageable gaps
- Below 55: skip

An excluded role always receives **SKIP**, regardless of keyword overlap.

## Evidence rules

### Never

1. Fabricate experience, metrics, technologies, publications, awards, or work authorization.
2. Turn academic ML work into professional AI/ML engineering.
3. Change team projects into sole ownership.
4. Convert “300+ reports over six months” into an unsupported monthly number.
5. State that the thesis is complete or has achieved results while it is in progress.
6. Submit an application or send outreach without explicit authorization.
7. Treat a generic careers homepage as a verified active job.

### Always

1. Map each job requirement to an exact canonical source.
2. Label evidence as professional, training, virtual experience, or academic.
3. Surface missing requirements and hard blockers.
4. Validate job title, location, description, and application route.
5. Deduplicate against `data/pipeline.md`, `data/application-tracker.md`, and `data/applied-companies.md`.
6. Keep candidate-facing language direct, specific, and ATS-readable.
7. For an explicitly requested number of companies/resumes, continue discovery
   through rejected/expired/duplicate leads until that many eligible live JDs
   are secured or the documented search is exhausted.

## Job-link validation

A posting is active only when:

1. The page loads without an expiry/closure message.
2. The page identifies the specific role and company.
3. The location and job description are visible.
4. An application route is present.

Generic career portals require a manual search for the exact role and must be marked `NEEDS_MANUAL_CHECK` until confirmed.

## Resume rules

- Start from `templates/resume-base.tex`.
- Generate a complete document from `\documentclass` through `\end{document}`.
- Preserve truthful dates and in-progress labels.
- Use keywords only when the underlying experience supports them.
- Prefer readable sections and conventional headings over keyword stuffing.
- Use a saved JD snapshot and map required/preferred requirements separately.
- Research a target-company problem only from the verified JD or dated authoritative company sources; record source, date, confidence, and whether the conclusion is explicit or inferred.
- Select exactly two distinct resume-ready projects from `context/evidence.yml`. Research can rank projects but cannot create experience.
Disclosure update (2026-09-09): include client names and the Irish phone exactly as supplied, as Chetan requested. Conflicting dates and unverified outcomes remain unresolved.
- Compile and hard-fail unless the PDF is exactly two A4 pages.
- Run `python3 scripts/validate_resume.py <resume.tex> --compile --output <resume.pdf> --render-dir <resume-preview> --qa-json <qa.json>` before release.
- Save exactly these required paths together for every passed job: `job-description.md`, `evaluation.md`, `company-research.md`, `evidence-map.yml`, `resume.tex`, `resume.pdf`, `resume-preview/page-01.png`, `resume-preview/page-02.png`, and `qa.json`.
- Rebalance relevance-ranked content for at most three attempts; never solve overflow by shrinking below the template's fixed font/margins.
- Report a supported-requirement-coverage diagnostic, not an unverifiable “ATS match.”
- Never use facts from `../backup/previous-backups/` or old job-list company briefs.

## Three separate decisions

Never blend these into one flattering number:

1. **Job fit** — whether the opportunity is worth pursuing.
2. **Supported requirement coverage** — how much of the JD is backed by evidence IDs; required items matter more than preferred items.
3. **Artifact QA** — binary release gates for provenance, two projects, successful compilation, exactly two pages, ATS-readable structure, and no unresolved/unsafe content.

A failed artifact gate is a failed resume regardless of job-fit or coverage score.


Current tracking contract: `data/career.db` is authoritative. `data/pipeline.md`, `data/application-tracker.md` and `data/applied-companies.md` are generated projections; do not edit them directly. Read live records with `python3 scripts/career.py jobs`, add via `add --file <job.json>`, and record user-reported status via `update`. Preparing a PDF never establishes an application.
