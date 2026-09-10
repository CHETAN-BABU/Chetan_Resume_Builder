# Data Contract

This contract prevents generated job/company content from contaminating Chetan's profile.

## Candidate-owned truth layer

These files may change only when Chetan supplies evidence or explicitly approves a correction:

- `config/profile.yml`
- `context/evidence.yml`
- `context/sources/career.md`
- `context/sources/masters-projects.md`
- `context/sources/portfolio-audit.md`
- `context/PROFILE-NOTES.md`
- `context/PROFILE.md`
- `interview-prep/story-bank.md`

Agents may identify gaps but must not auto-promote target-JD terms, company technologies, proposed work, or inferred results into this layer.

### Evidence registry schema

Every entry under `claims` and `projects` in `context/evidence.yml` requires a non-empty `source_refs` list. Every resume-ready project requires a `resume_content` mapping with exactly these keys:

```yaml
resume_content:
  title: "Non-empty text"
  context: "Non-empty text"
  bullets:
    - "Non-empty bullet"
    - "Non-empty bullet"
```

`bullets` must contain two or three non-empty strings. The registered title, context, and bullets are the exact visible project block; tailoring may select the block but may not paraphrase it.

## System logic layer

These files define reusable behavior and may be improved without changing candidate facts:

- `AGENTS.md`
- `.github/agents/*.agent.md`
- `workflows/*.md`
- `workflows/modes/*.md`
- `scripts/*`
- `templates/*`
- `README.md`
- `docs/CLEANUP-REPORT.md`

## Renderer

`templates/resume-base.tex` is a fixed base renderer populated only from approved evidence. It is not a factual source.

## Generated job layer

Every passed job has one isolated `output/**/{job-id}/` folder with exactly these required artifact paths:

```text
job-description.md
evaluation.md
company-research.md
evidence-map.yml
resume.tex
resume.pdf
resume-preview/page-01.png
resume-preview/page-02.png
qa.json
```

They may cite candidate evidence IDs, but they never update the truth layer automatically.

## Rule

Company research can decide which real evidence is relevant. It can never create candidate evidence.
