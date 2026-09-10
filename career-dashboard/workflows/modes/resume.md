# Mode: Resume — Evidence-Grounded Two-Page Tailoring

Use this only after the job is verified, eligible, and evaluated.

## Required inputs

- Saved JD snapshot: `output/applications/{job-id}/job-description.md`
- Eligibility/evaluation with normalized requirement IDs: `output/applications/{job-id}/evaluation.md`
- Company research: `output/applications/{job-id}/company-research.md`
- Candidate revision from `config/profile.yml`
- Claim/project registry: `context/evidence.yml`
- Fixed renderer: `templates/resume-base.tex`

Do not generate a company-tailored resume from only a title and employer name.

## Content plan

Write `output/applications/{job-id}/evidence-map.yml` before editing LaTeX:

```yaml
  candidate_revision: "2026-09-09.1"
job_id: "..."
role_eligible: true
job_snapshot_sha256: "..."
supported_requirement_coverage: 0
requirements:
  - id: "R01"
    priority: "required"
    text: "..."
    evidence_ids: ["..."]
    strength: "strong|partial|gap"
company_problem:
  statement: "..."
  source_url: "..."
  published_or_accessed: "YYYY-MM-DD"
  evidence_class: "explicit|inferred"
  confidence: "high|medium|low"
selected_project_id: "PROJ-..."
selected_project_reason: "..."
resume_claim_ids: ["..."]
held_claims_used: []
```

Every candidate claim in the content plan needs an evidence ID. Company facts are not candidate evidence and may not be copied into the skills or experience sections.

When an academic or candidate project is selected:

- `PROJ-RAG-CHATBOT`: project skills may cite `SKILL-GENAI-001` and must remain separate from professional experience; do not add the held evaluation score or unreviewed Docker/Kubernetes/GitHub Actions details.
- `PROJ-SECOM-FAULT-DETECTION` or `PROJ-FAANG-PCA`: project skills may cite `SKILL-ML-TOOLING-001`; do not present sample variance as model accuracy or claim production/business impact.
- `PROJ-MSC-FRAUD`: use the audited results only with limited-discrimination and no-production-readiness wording; do not imply a final MSc grade.
- `PROJ-CLUSTERING-DBSCAN`: project skills may cite `SKILL-CLUSTERING-001`; retain the failed ring-recovery limitation.
- `PROJ-EU-COMPLIANCE-RAG`: project skills may cite `SKILL-GENAI-LOCAL-001`; do not claim legal correctness, calibrated confidence, benchmarked accuracy, or deployment.
- `PROJ-POWERBI-PORTFOLIO`: project skills may cite `SKILL-BI-PORTFOLIO-001`; do not add undocumented DAX, Power Query, schema, or business-impact claims.
- `PROJ-BLOGBOARD`: project skills may cite `SKILL-AGENTIC-001`; do not claim autonomous production publishing, successful deployment, traffic, or content-quality metrics.
- Keep professional BI skills and candidate-project skills explicitly labelled so the reader can distinguish evidence type.

## Exactly-one-project selection

1. Read all resume-ready projects in `context/evidence.yml`.
2. Score them using `config/profile.yml > project_selection > ranking_weights`.
3. Prefer professional completed evidence for BI roles and the academic thesis only for eligible junior/graduate data-science or directly relevant fraud/health analytics roles.
4. Write one selected project using its real external name, ownership, evidence type, status, and approved facts.
5. Use the registry's `resume_content` title/context/bullets exactly so automated QA can bind visible text to the selected ID.
6. Do not create a second project block, turn coursework into a project, or imply work for the target employer.
7. If the match is weak, say so in the evidence map; do not manufacture a stronger project.

## Fixed content budgets

Keep the template layout and typography unchanged.

| Slot | Budget |
|---|---|
| Professional Summary | 55–80 words |
| Core Skills | 10–16 supported phrases |
| Associate Analyst experience | 6–8 bullets |
| Training-role experience | 2–3 bullets |
| Selected Project | one title/context and 2–3 bullets; 70–120 words |
| Education | 2–4 concise lines |
| Certifications | verified names only |
| Technical Skills | 4–5 compact evidence-backed categories |

Use action, scope, method, and supported result. A quantified result is optional; never invent one merely to fit a bullet formula.

## Rendering loop

1. Copy the complete LaTeX template into `output/applications/{job-id}/resume.tex`.
2. Change only content slots and project fields; preserve the fixed layout contract.
3. Run:

   `python3 scripts/validate_resume.py output/applications/{job-id}/resume.tex --compile --output output/applications/{job-id}/resume.pdf --render-dir output/applications/{job-id}/resume-preview --qa-json output/applications/{job-id}/qa.json`

4. If the validator fails for length:
   - Over two pages: remove the lowest-relevance optional bullet, de-duplicate skills, or tighten supported wording.
   - Under two pages: add the highest-relevance unused supported detail or a stronger evidence-backed bullet.
5. Retry at most three times. Never shrink the font, margins, or line spacing.
6. Confirm `resume-preview/page-01.png` and `resume-preview/page-02.png` are the only preview images.
7. Release only when every hard gate passes and visual review is recorded.

## Output report

Return:

- eligibility decision and job-fit score;
- supported requirement coverage with required gaps;
- selected project ID and why it matches the sourced company problem;
- paths to all nine required artifacts: `job-description.md`, `evaluation.md`, `company-research.md`, `evidence-map.yml`, `resume.tex`, `resume.pdf`, `resume-preview/page-01.png`, `resume-preview/page-02.png`, and `qa.json`;
- any missing fact Chetan should confirm.

Never promise an interview or shortlist.
