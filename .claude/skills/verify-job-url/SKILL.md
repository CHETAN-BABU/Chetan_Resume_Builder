---
name: verify-job-url
description: Verify one job URL or URLs in Chetan's Markdown pipeline/tracker and classify them as likely active, expired, broken, or requiring manual review. Use before adding, refreshing, or acting on an Ireland job lead.
---

# Verify Job URL

This is the Claude entry point for the workspace's existing checker. The script,
the result classes and the role gate are shared with every other assistant:
read `career-dashboard/.agents/skills/verify-job-url/SKILL.md` for the full
instructions and keep the two in step.

Run it from `career-dashboard/`:

```bash
python3 .agents/skills/verify-job-url/scripts/verify_job_url.py \
  --url "https://company.example/jobs/123" \
  --output data/verification-results.json
```

```bash
python3 .agents/skills/verify-job-url/scripts/verify_job_url.py \
  --file data/pipeline.md \
  --delay 8 \
  --output data/verification-results.json
```

`LIKELY_ACTIVE` still needs a manual check of title, company, Ireland location,
description and application route. URL liveness is not profile fit: apply the
role gate in `config/profile.yml` afterwards. Never delete applied-job history.
