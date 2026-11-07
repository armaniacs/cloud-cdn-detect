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

- **Passive observation only.** Ordinary `curl` requests, `dig`, `whois`, TLS certificate inspection, official IP-range feeds, and public web information. No port scans, no directory brute-forcing, no vulnerability probing, no high-volume requests, no on-demand scans.
- **Facts and inference stay separate.** Every conclusion is paired with the raw observations (headers, DNS, whois output) that support it — no unsupported assertions.
- **Confidence is explicit and scored.** Weighted signals (`S_total = min(100, Σ w_i)`) map to high (≥60) / medium (40–59) / low (<40). A lone header never exceeds low.
- **Stacks split into three slots.** Edge (CDN/WAF) / Platform (PaaS) / Origin (IaaS/hosting) are reported separately instead of a single winner.
- **The signature database grows.** When an unknown signature shows up, its origin is researched via web search before it is added to `references/provider-signatures.md`.
- **Japanese provider coverage.** Sakura Internet (including Enhanced LB and Web Accelerator), Xserver, GMO group (ConoHa / lolipop / heteml), and IIJ — alongside AWS, Google Cloud, Cloudflare, Fastly, Akamai, Vercel, Netlify, and more.
- **Emerging/regional coverage (cdncheck-derived).** Tencent EdgeOne, Gcore, Imperva, Sucuri, ArvanCloud, CDNetworks, Baidu, Huawei, Leaseweb/Qrator/F5 et al. — verify when it matters.

## How it works

| Step | What happens |
|---|---|
| 1. Decompose the target | Separate the main site (apex / www), app, API, static assets, status page, and marketing site — they often live on different infrastructure |
| 2. HTTP headers | `curl -sIL https://<domain>` — check `server`, `via`, `x-amz-*`, `x-cache`, `cf-*`, `x-vercel-id`, `server-timing`, and more |
| 3. DNS | `dig +short <host>` (A / AAAA), `dig +short <host> CNAME` — for apex, www, app, api, cdn, static, etc. |
| 4. whois | `whois <ip>` — netname / descr / OrgName, the registered owner of the IP |
| 5. ASN | Cymru whois/DNS → RIPEstat → RDAP (APNIC-first) for IP→AS; PeeringDB (`/api/net?asn=`) for ASN-to-org corroboration |
| 5c. IP ranges | Official feeds: AWS / GCP / Azure (cached) / Cloudflare / Fastly / GitHub Pages. Akamai, Vercel, Netlify, Shopify, and JP hosts publish no machine-readable feed |
| 6. TLS certificate | `openssl s_client` plus crt.sh (`?q=%25.<domain>&output=json`) for issuer corroboration |
| 7. Signature match | Four layers (network / DNS chain / transport / app) against [`references/provider-signatures.md`](./references/provider-signatures.md), then weighted score `S_total` |
| 8. Web cross-check | Provider case studies, operator engineering blogs, plus bgp.he.net / MXToolBox / Radar / urlscan (read-only; never Rescan). Shodan/Censys/VT only with a key, past data only |
| 9. Report | Edge / Platform / Origin slots + evidence table + score + caveats |

## Evidence hierarchy

1. **whois / RDAP / ASN** — registered owner of the IP. Nearly conclusive
2. **HTTP headers / CNAME / TLS certificate** — implementation signatures. Strong, but can be rewritten or stripped
3. Provider-published IP ranges (AWS, GCP, Azure Service Tags, Cloudflare, Fastly, GitHub Pages)
4. Public statements (official blogs, case studies, job postings)
5. Third-party databases (PeeringDB, crt.sh, urlscan past results, MXToolBox, Radar, bgp.he.net; Wappalyzer / BuiltWith / Netcraft) — indicative only

## Report format

```markdown
## Conclusion
Edge: <CDN/WAF> / Platform: <PaaS or n/a> / Origin: <IaaS/hosting or unknown>
(score S_total, confidence: high/medium/low)

## Evidence
| Observation | Result | Suggests |
|---|---|---|
| HTTP header | x-amz-cf-id: … | Edge: AWS CloudFront (+10) |
| DNS | A 54.239.163.x | Edge: CloudFront (+35 feed) |
| whois | OrgName: Amazon Technologies Inc. | Origin: AWS |

## Caveats
- … (CDN confirmed but origin unidentified, marketing site on a different provider, etc.)
```

**Confidence levels (score-mapped)**

- **High (≥60, Definitive)**: multiple independent high-weight signals agree, no contradictions
- **Medium (40–59, Probable)**: signals agree but come from a single source, or public confirmation is missing or outdated
- **Low (<40, Heuristic)**: weak clues, contradictions, or limited observation scope

## Signature database

`references/provider-signatures.md` maps observed signals to providers:

- **AWS** — CloudFront, S3 static hosting, API Gateway, ELB, ACM-issued certificates
- **Google Cloud** — Cloud Storage, GFE (`via: 1.1 google`), Cloud Functions
- **CDNs** — Cloudflare, Fastly, Akamai, Azure Front Door / Azure CDN; emerging/regional (Tencent EdgeOne, Gcore, Imperva, Sucuri, ArvanCloud, CDNetworks, Baidu, Huawei — cdncheck-derived)
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

See [CONTRIBUTING.md](./CONTRIBUTING.md) ([日本語](./CONTRIBUTING-ja.md)) for the checklist, and the docs site
`https://armaniacs.github.io/cloud-cdn-detect/` for browsable signatures and changelog.

## Repository structure

```text
cloud-cdn-detect/
├── SKILL.md                       # The skill: investigation procedure and reporting rules
├── README.md                      # This file
├── CHANGELOG.md                   # Notable changes (Keep a Changelog format)
└── references/
    └── provider-signatures.md     # Signature lookup table (grows with each observation)
```

## Listing on skills.sh

skills.sh has no submission form. Skills are listed automatically through install telemetry: once this repo is public on GitHub, the first `npx skills add armaniacs/cloud-cdn-detect` registers it.
