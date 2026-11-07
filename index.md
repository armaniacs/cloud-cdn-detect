---
layout: default
title: cloud-cdn-detect
---

**English** | [日本語](./index-ja.html)

# cloud-cdn-detect

Identify which cloud, CDN, or hosting provider runs behind a website, API,
or domain — using passive observation only. Every report separates observed
facts from inference and comes with an evidence table and a confidence level.

```bash
npx skills add armaniacs/cloud-cdn-detect
```

## Docs

- [Skill workflow (SKILL.md)](./SKILL.html) — investigation procedure and reporting rules
- [Provider signatures](./references/provider-signatures.html) — header / DNS / ASN / TLS lookup table
- [Changelog](./CHANGELOG.html) — notable changes
- [Contributing](./CONTRIBUTING.html) — add a signature, file an issue, review the schema design

## Report shape

```markdown
## Conclusion
Edge: <CDN/WAF> / Platform: <PaaS or n/a> / Origin: <IaaS/hosting or unknown>
(score S_total, confidence: high/medium/low)
```

Passive observation only: ordinary `curl`, `dig`, `whois`, TLS inspection,
official IP-range feeds, and public web info. No port scans, no on-demand scans.
