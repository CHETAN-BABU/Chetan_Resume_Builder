# Mode: Evaluate — Job Fit

Evaluate a specific job description or URL using Chetan's real professional and academic evidence.

## Step 0 — Eligibility gate

Classify the job as:

- Analytics
- BI Delivery
- Applied Data Science — Emerging
- GenAI Applications — Project Track
- Excluded

If the role requires professional production AI/ML engineering, software/full-stack, DevOps/MLOps, hardware/embedded, or production-pipeline Data Engineering, stop with `SKIP — outside Chetan's profile`. Entry-level retrieval-application roles pass only when the registered RAG project covers the requirements and the employer accepts project evidence.

## A. Role summary

| Field | Value |
|------|-------|
| Company | |
| Role | |
| Track | Analytics / BI Delivery / Applied Data Science / GenAI Applications |
| Seniority | |
| Location/arrangement | |
| Posting status | Active / Needs manual check / Expired |
| Eligibility | Pass / Conditional / Excluded |

## B. Evidence match

Read `context/evidence.yml` and `context/sources/career.md`. Normalize each distinct JD requirement before matching:

| Requirement ID | Required/preferred | Job requirement | Evidence ID(s) | Chetan evidence | Evidence type/status | Strength |
|---|---|---|---|---|---|---|
| R01 | Required | Power BI | project/claim IDs | Enterprise dashboard work | Professional | Strong |
| R02 | Preferred | Classification | `PROJ-MSC-FRAUD` | In-progress fraud thesis | Academic, in progress | Developing |
| R03 | Required | Missing requirement | None | Gap | None | Weak |

For each gap, state whether it is a blocker, a manageable gap, or a nice-to-have. Never turn coursework into professional deployment experience.

Compute **supported requirement coverage** separately from job priority:

- Required requirement: weight 3
- Preferred requirement: weight 1
- Strong supported evidence: credit 1.0
- Adjacent/partial supported evidence: credit 0.5
- Gap or held evidence: credit 0

Report the weighted percentage with blockers. This is a transparent evidence diagnostic, not an ATS score and not a shortlist prediction.

## C. Seniority and competition

Assess:

- Required years versus Chetan's dated Feb 2023–Jan 2025 experience
- Graduate/junior wording
- Applicant count when visible
- Posting age and reposting signals
- Specialist Power BI/BI requirements that improve fit
- Contradictory or unrealistic requirements

## D. Location and work requirements

Report only what the posting and current profile establish:

- Ireland location and on-site/hybrid/remote arrangement
- Sponsorship or work-authorization wording from the posting
- Chetan's supplied visa-validity date
- Any uncertainty requiring confirmation

Do not provide unverified immigration conclusions.

## E. Tailoring plan

Give the top five truthful changes:

- summary emphasis
- skill ordering
- professional bullets
- academic project emphasis when relevant
- unsupported keywords to avoid
- ranked project candidates and the one selected real project ID

## F. Interview preparation

Map three to five evidence-backed stories from `interview-prep/story-bank.md`. Remove any unsupported detail before use.

## Decision

Apply the weighted score in `workflows/modes/_shared.md`, then return:

- 85–100: APPLY PROMPTLY
- 70–84: WORTH APPLYING
- 55–69: CONDITIONAL
- Below 55: SKIP

Also return the separate supported-requirement-coverage percentage and any hard requirement gaps. Do not average it with artifact QA.

Save the complete evaluation to the isolated job folder as `evaluation.md`. This is a required per-job artifact and must include the eligibility decision, job-fit score, normalized requirement IDs, evidence mappings, supported requirement coverage, blockers, and tailoring plan.

Record actual application status through the dashboard or `scripts/career.py update`. The tracker Markdown is a generated projection. Evaluation alone does not authorize an application.
