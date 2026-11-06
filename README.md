# cloud-cdn-detect

[![skills.sh](https://skills.sh/b/armaniacs/cloud-cdn-detect)](https://skills.sh/armaniacs/cloud-cdn-detect)

Identify which cloud, CDN, or hosting provider runs behind a website, API, or domain — using passive observation only. Every report separates observed facts from inference and comes with an evidence table and a confidence level.

Ask things like:

- "Where is this service hosted?"
- "Which cloud does this API run on?"
- "What CDN does this site use?"
- "Is this AWS, Cloudflare, Sakura, or Xserver?"（このサービス、どこで動いてる？）

## Install

```bash
npx skills add armaniacs/cloud-cdn-detect
```

Works with any agent that supports the agent-skills format — Claude Code, OpenCode, Cursor, Codex, GitHub Copilot, and more. The CLI installs the skill into every compatible agent directory it finds. Once installed, the skill triggers automatically on the questions above.

To check discovery without installing:

```bash
npx skills add armaniacs/cloud-cdn-detect --list
```

## What it does

- **Passive observation only.** Ordinary `curl` requests, `dig`, `whois`, TLS certificate inspection, and public web information. No port scans, no directory brute-forcing, no vulnerability probing, no high-volume requests.
- **Facts and inference stay separate.** Every conclusion is paired with the raw observations (headers, DNS, whois output) that support it — no unsupported assertions.
- **Confidence is explicit.** "High" requires multiple independent signatures (e.g. whois/ASN plus headers/CNAME) agreeing without contradiction.
- **The signature database grows.** When an unknown signature shows up, its origin is researched via web search before it is added to `references/provider-signatures.md`.
- **Japanese provider coverage.** Sakura Internet (including Enhanced LB and Web Accelerator), Xserver, GMO group (ConoHa / lolipop / heteml), and IIJ — alongside AWS, Google Cloud, Cloudflare, Fastly, Akamai, Vercel, Netlify, and more.

## How it works

| Step | What happens |
|---|---|
| 1. Decompose the target | Separate the main site (apex / www), app, API, static assets, status page, and marketing site — they often live on different infrastructure |
| 2. HTTP headers | `curl -sIL https://<domain>` — check `server`, `via`, `x-amz-*`, `x-cache`, `cf-*`, `x-vercel-id`, `server-timing`, and more |
| 3. DNS | `dig +short <host>` (A / AAAA), `dig +short <host> CNAME` — for apex, www, app, api, cdn, static, etc. |
| 4. whois | `whois <ip>` — netname / descr / OrgName, the registered owner of the IP |
| 5. ASN | `whois -h whois.cymru.com " -v <ip>"` — the announcing AS and organization |
| 6. TLS certificate | `openssl s_client` — issuer and SAN can reveal the CDN or operator |
| 7. Signature match | Compare observations against [`references/provider-signatures.md`](./references/provider-signatures.md) |
| 8. Web cross-check | Provider case studies, operator engineering blogs, job postings, Wappalyzer / BuiltWith / bgp.he.net |
| 9. Report | Conclusion + evidence table + caveats + confidence |

## Evidence hierarchy

1. **whois / ASN** — registered owner of the IP. Nearly conclusive
2. **HTTP headers / CNAME / TLS certificate** — implementation signatures. Strong, but can be rewritten or stripped
3. Provider-published IP ranges (`https://ip-ranges.amazonaws.com/` etc.)
4. Public statements (official blogs, case studies, job postings)
5. Third-party databases (Wappalyzer / BuiltWith / Netcraft / bgp.he.net) — indicative only

## Report format

```markdown
## Conclusion
<domain> is estimated to run on <provider> (confidence: high/medium/low)

## Evidence
| Observation | Result | Suggests |
|---|---|---|
| HTTP header | x-amz-cf-id: … | AWS CloudFront |
| DNS | A 54.239.163.x | CloudFront edge |
| whois | OrgName: Amazon Technologies Inc. | AWS |

## Caveats
- … (CDN confirmed but origin unidentified, marketing site on a different provider, etc.)
```

**Confidence levels**

- **High**: multiple independent signatures agree (whois/ASN + headers/CNAME etc.), no contradictions
- **Medium**: signatures agree but come from a single source, or public confirmation is missing or outdated
- **Low**: weak clues, contradictions, or limited observation scope

## Signature database

`references/provider-signatures.md` maps observed signals to providers:

- **AWS** — CloudFront, S3 static hosting, API Gateway, ELB, ACM-issued certificates
- **Google Cloud** — Cloud Storage, GFE (`via: 1.1 google`), Cloud Functions
- **CDNs** — Cloudflare, Fastly, Akamai, Azure Front Door / Azure CDN
- **PaaS / hosting** — Vercel, Netlify, GitHub Pages, Heroku, Shopify, Wix, Squarespace
- **Japanese hosting** — Sakura Internet (Enhanced LB and Web Accelerator included), Xserver, GMO group, IIJ

Entries marked ✓ were verified by direct observation. Unmarked entries are established knowledge — re-verify when it matters.

## Known pitfalls

- **CDN ≠ origin.** What runs behind CloudFront / Cloudflare is invisible from outside; the observable fact ends at "uses Cloudflare as its CDN".
- **Marketing sites are often separate.** The product and its marketing site frequently run on different infrastructure.
- **PaaS runs on top of a cloud.** Vercel / Netlify / Heroku edge IPs whois to Amazon — that does not mean they use AWS directly. Prefer CNAME, headers, and `server-timing`.
- **SaaS is reported separately.** Zendesk / statuspage.io / Stripe etc. are reported as external SaaS in use, not as the company's infrastructure.
- **Missing signatures are not evidence of absence.** Reverse proxies and security products strip `Server` and vendor headers.
- **Edge IPs change.** Geo-distributed CDN IPs differ per request; observe multiple times to see the pattern.

## Real example

A real investigation of a Japanese SaaS, observed 2026-11-04 (service name, domains, and exact IPs withheld; observation values unchanged):

| Target | Observation | Conclusion |
|---|---|---|
| Service A — main site (www / apex) | `server: AmazonS3` + `x-amz-cf-id` + `via: 1.1 <hash>.cloudfront.net (CloudFront)` | S3 + CloudFront |
| Service A — API (`api.<domain>`) | A 35.73.152.x, whois `OrgName: Amazon Technologies Inc.`, AS16509 (AMAZON-02) | AWS Tokyo region |
| Service A — marketing site (separate domain) | netname `XSCLD` (Xserver Networks Inc.), AS131965 | Xserver |

→ Product on AWS, marketing site on Xserver (confidence: high) — a typical case of split infrastructure.

## Contributing

Found a signature not in the table? Verify its origin via web search, then open a PR adding it to `references/provider-signatures.md` (with a ✓ if you observed it yourself).

## Repository structure

```text
cloud-cdn-detect/
├── SKILL.md                       # The skill: investigation procedure and reporting rules
├── README.md                      # This file
└── references/
    └── provider-signatures.md     # Signature lookup table (grows with each observation)
```

## Listing on skills.sh

skills.sh has no submission form. Skills are listed automatically through install telemetry: once this repo is public on GitHub, the first `npx skills add armaniacs/cloud-cdn-detect` registers it.
