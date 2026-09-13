# From saved posting to reviewed resume

Read `../AGENTS.md`, `../config/profile.yml`, `../context/evidence.yml` and the question queue first.

1. Verify the specific posting in a browser and save the complete JD, original URL and access date. A career homepage or logged-out error page is not a verified vacancy.
2. Evaluate every essential requirement, seniority, Ireland location and actual work-permission conditions. Set `role_eligible` to true only after the role decision is supported. Record constraints in evaluation.md; exclude ineligible roles.
3. Research the employer using current primary sources. Record explicit statements separately from inference. Explain which actual employer problem makes the selected project relevant; do not turn employer research into candidate experience.
4. Prepare the draft through the dashboard or `scripts/career.py`. Select exactly two distinct `resume_ready` projects. The initial summary and other experience remain the approved base wording; tailor them to the JD without strengthening claims.
5. Complete evidence-map.yml. Each requirement needs an ID, priority, exact requirement text, evidence IDs and `strong`, `partial` or `gap` strength. Compute supported coverage using required weight 2, preferred weight 1, strong 1, partial 0.5, gap 0. No evidence is a gap. Keep registry revision and saved-JD hash correct.
6. Run full validation. Resolve all failures in the source/evidence map. Compile to two A4 pages, inspect both images for clipping, layout and readable text. Confirm candidate claims and selected-project wording, source status, dates and attribution.
7. Record visual review with the validator only after seeing the latest pages. Keep all artifacts together. Do not carry a QA pass forward after modifying the resume or registry.
8. Prepare the user-facing recommendation and files. Application submission and external messages require explicit user authorisation.

The local dashboard stores jobs in data/career.db and shows all PDFs as drafts unless their current source, PDF, evidence revision and review status match. Its actions do not submit applications or run paid model calls.
