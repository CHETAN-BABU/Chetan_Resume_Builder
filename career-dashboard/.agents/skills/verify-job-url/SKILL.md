---
name: verify-job-url
description: Verify one job URL or URLs in Chetan's Markdown pipeline/tracker and classify them as likely active, expired, broken, or requiring manual review. Use before adding, refreshing, or acting on an Ireland job lead.
---

# Verify Job URL

Use the bundled script for deterministic HTTP and expiry checks, then manually confirm any role before treating it as active.

## Single URL

```bash
python3 .agents/skills/verify-job-url/scripts/verify_job_url.py \
  --url "https://company.example/jobs/123" \
  --output data/verification-results.json
```

## Markdown batch

The parser supports pipeline lines such as:

```text
- [ ] https://company.example/jobs/123 | Example Co | Data Analyst | Analytics | Dublin
```

Run:

```bash
python3 .agents/skills/verify-job-url/scripts/verify_job_url.py \
  --file data/pipeline.md \
  --delay 8 \
  --output data/verification-results.json
```

## Interpret results

- `LIKELY_ACTIVE`: HTTP and page-text checks passed. Manually confirm title, company, Ireland location, description, and application route.
- `EXPIRED`: Closure text or a redirect from a specific job to a generic career page was detected.
- `BROKEN`: HTTP/network failure.
- `NEEDS_MANUAL_CHECK`: Generic portal, auth wall, or insufficient page evidence.

URL liveness does not establish profile fit. After verification, apply the role gate in `config/profile.yml`; exclude AI/ML/GenAI roles requiring professional production engineering, software/MLOps, hardware, and engineering-heavy Data Engineer roles.

Do not delete applied-job history. Mark closed postings in `data/application-tracker.md`.
