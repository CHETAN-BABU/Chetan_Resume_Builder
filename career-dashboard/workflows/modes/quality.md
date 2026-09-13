# Mode: Quality — Resume Release Gate

Artifact QA is binary. It is not averaged with job fit or supported requirement coverage.

The release folder must contain exactly these required artifact paths: `job-description.md`, `evaluation.md`, `company-research.md`, `evidence-map.yml`, `resume.tex`, `resume.pdf`, `resume-preview/page-01.png`, `resume-preview/page-02.png`, and `qa.json`.

## Automated hard gates

Run `scripts/validate_resume.py` and require:

- LaTeX compiles without an overfull box or unresolved reference warning.
- PDF page count is exactly 2.
- A4 single-column template and minimum 10pt body type are preserved.
- Exactly one `Selected Project` rendering block and one registered project ID are present.
- Project ID exists in `context/evidence.yml`.
- No unresolved placeholders, example candidate identity, unsafe claims, contact details contrary to the current profile policy, visible evidence IDs, or prohibited filler.
- Required headings, identity, email, LinkedIn, employment dates, MSc in-progress status, and PDF metadata are present.
- No page has suspiciously little source content.
- The PDF is newer than or as new as its LaTeX source.

## Evidence review

The evidence map must show:

- candidate revision and JD snapshot hash;
- one evidence mapping per normalized JD requirement;
- all resume claim IDs;
- no held claims;
- two selected project IDs;
- ownership/status wording preserved;
- current-company problem source, date, confidence, and explicit/inferred label.

Reject if a JD keyword was converted into an unsupported skill, a team result became individual ownership, academic work became professional experience, or a reported result became an independently verified fact.

## Manual visual gate

Inspect rendered images of both pages for:

- clipping, overlap, tiny text, or crowded contact details;
- orphan headings or split entries;
- unbalanced blank space;
- link styling and readable hierarchy;
- a genuine second page rather than a blank or nearly blank page.

The only required preview files are `resume-preview/page-01.png` and `resume-preview/page-02.png`.

Rerun validation with `--visual-review pass --visual-reviewer "{identity}"`. Do not edit QA JSON manually. The final manifest must bind the reviewer/timestamp to the PDF and exact two preview hashes.

## Release result

Return either:

- `PASS — release-ready`, with artifact paths; or
- `FAIL — do not use`, with exact failures and the next evidence-safe repair.
