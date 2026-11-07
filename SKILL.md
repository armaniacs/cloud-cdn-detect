---
name: cloud-cdn-detect
description: >-
  Identify which cloud, CDN, or hosting provider runs behind a website, API,
  or domain using passive observation only (curl, dig, whois, TLS
  certificates, public web info). Use for any request like "Where is this
  service hosted?", "Which cloud does this run on?", "What CDN does this
  site use?", "Is this AWS, Cloudflare, Sakura, or Xserver?", 「このサービス、
  どこで動いてる？」, 「インフラどこのクラウド？」. Reports separate observed
  facts from inference and include an evidence table and a confidence
  level. Never performs active scanning (port scans, vulnerability
  probing, or high-volume requests).
---

# cloud-cdn-detect — Identifying cloud / CDN / hosting providers (passive observation)

Identify the cloud provider, CDN, or hosting company behind a target web service, API, or domain using only passive observation from the outside, and report the findings with evidence and confidence levels.

Use `references/provider-signatures.md` as the signature lookup table.

## Ground rules

1. **Passive observation only.** The only things allowed without permission:
   - Ordinary requests via `curl` (HEAD, a few GETs if needed, following redirects with `-L`)
   - `dig` / `whois` / `openssl s_client` (TLS certificate inspection)
   - Searching and reading public web information
2. **Forbidden**: port scanning, directory discovery, requests that exploit vulnerabilities, high volumes of requests in a short time. Only with explicit permission from the target, and only within the instructed scope.
3. **Separate observation from inference.** Facts (raw header / DNS / whois output) and interpretations ("concluded CloudFront") must correspond in the report; never state conclusions without evidence.
4. Always note that conclusions are technical estimates, not official statements by the provider.

## Evidence hierarchy

1. **whois / ASN** — registered owner of the IP. Nearly conclusive
2. **HTTP headers / CNAME / TLS certificates** — implementation-derived signatures. Strong but can be rewritten or stripped
3. Provider-published IP ranges (`https://ip-ranges.amazonaws.com/` etc.)
4. Public statements on the web (official blogs, case studies, job postings)
5. Third-party databases (Wappalyzer / BuiltWith / Netcraft / bgp.he.net) — indicative only

Treat confidence as "high" only when multiple independent signatures agree.

## Workflow

### 1. Decompose the target
Distinguish the main site (apex / www), app (app.), API (api.), login, static assets (cdn / assets / static / img), status page, and marketing site (often on a separate domain). When asked about "the service's infrastructure", prioritize the main site and API, and remember the marketing site may be on different infrastructure.

### 2. Observe HTTP headers
```bash
curl -sI https://<domain>     # HEAD
curl -sIL https://<domain>    # follow redirects
```
- Headers to check: `server`, `via`, `x-amz-*`, `x-cache`, `x-served-by`, `x-vercel-id`, `cf-*`, `x-azure-ref`, `x-goog-*`, `x-nf-request-id`, `x-shopid`, `x-wix-request-id`, `server-timing`
- Some configurations return errors for HEAD (e.g. `x-cache: Error from cloudfront`). Don't jump to conclusions; try GET or another path once
- `server-timing` can leak the PaaS backend (`aws-nrt` etc.)

### 3. Resolve DNS (resolver-aware)

First, record your own resolver (`scutil --dns` on macOS, `/etc/resolv.conf`, or `systemd-resolve --status` on Linux).
Then resolve explicitly:

```bash
dig +short <host>                  # A / AAAA via system-default (record which resolver this was)
dig +short <host> @1.1.1.1         # Cloudflare
dig +short <host> @8.8.8.8         # Google
dig +short <host> CNAME @1.1.1.1
```

Record the resolver, timestamp, TTL, and whether CNAME was absent for every row in the Evidence table.
- Candidates: apex, www, app, api, login, admin, status, cdn, assets, static, img
- Root domains can hide CNAMEs behind ALIAS / direct A records (verified example: CloudFront IPs set directly as A records)

### 4. whois (IP ownership)
```bash
whois <ip> | grep -iE "orgname|netname|descr|owner"
```
- macOS `whois` follows referrals across registries automatically. Don't confuse ARIN referral records (`OrgName: Asia Pacific Network Information Centre` etc.) with actual data
- `owner` can hit ARIN comment lines ("correct owner of the IP address") — skip them

### 5. ASN (Team Cymru)
```bash
whois -h whois.cymru.com " -v <ip>"    # IP → AS (verbose, includes BGP prefix and registry)
whois -h whois.cymru.com AS<number>    # AS → organization
```
Comma-separated multiple lookups and piped bulk queries do not work with macOS `whois`. Run them one at a time.

### 6. TLS certificate (optional)
```bash
echo | openssl s_client -connect <host>:443 -servername <host> 2>/dev/null \
  | openssl x509 -noout -subject -issuer
```
- SAN can contain the CDN provider's domain (`*.cloudfront.net` etc.)
- The issuer is a clue too: `Amazon RSA 2048 M01` (AWS ACM), Google Trust Services, Let's Encrypt, etc.

### 7. Match signatures
Compare against `references/provider-signatures.md`. **When a signature not in the table appears, verify its origin via web search before appending it to that file** (this skill is designed to grow with every observation). Never append a signature with an unconfirmed origin, and never record the service you observed it on — append the signature and its technical source (official documentation etc.) only, so third-party target names stay out of this repository.

### 8. Cross-check on the web
- Provider side: case studies / press releases from AWS / Google Cloud / Azure / Cloudflare etc.
- Operator side: official blogs, engineering blogs (Zenn / Qiita / Hatena), engineer job postings
- Third party: Wappalyzer, BuiltWith, Netcraft, bgp.he.net
- Example queries: `"<domain>" AWS`, `"<company>" case study cloud`, `"<company>" engineer hiring AWS`, `"<社名>" 導入事例 クラウド`

### 9. Report
```markdown
## Conclusion
<domain> is estimated to run on <provider> (confidence: high/medium/low)

## Evidence
| Observation | Resolver | Result | Suggests |
|---|---|---|---|
| HTTP header | system-default | x-amz-cf-id: … | AWS CloudFront |
| DNS | @1.1.1.1 | A 54.239.163.x | CloudFront edge |
| whois | system-default | OrgName: Amazon Technologies Inc. | AWS |

## Caveats
- … (CDN confirmed but origin unidentified, marketing site on a different provider, etc.)
```

**Confidence definitions**
- **High**: multiple independent signatures agree — whois/ASN plus headers/CNAME etc., no contradictions
- **Medium**: signatures agree but come from a single source, or public confirmation is missing or outdated
- **Low**: weak clues, contradictions, or limited observation scope

## Pitfalls

1. **CDN ≠ origin**: the origin server behind CloudFront / Cloudflare is essentially invisible from outside. The observable fact ends at "uses CloudFront as its CDN"
2. **Marketing sites are separate**: even under the same operator, corporate/marketing sites and the service itself often run on different infrastructure
3. **PaaS sits on top of a cloud**: whois for Vercel / Netlify / Heroku edge IPs returns Amazon etc. That does not mean "uses AWS directly". Prefer CNAME, headers, and `server-timing`
4. **Vanity CNAMEs**: `cdn.example.com` → `dxxx.cloudfront.net` — the company's own domain pointing at a CDN
5. **Multi-CDN**: combinations of multiple CDNs and GSLBs exist. Don't generalize from one or two observations
6. **SaaS is a separate category**: Zendesk / statuspage.io / Stripe / Google speech recognition etc. are reported separately as "external SaaS in use"
7. **Overlapping IP ranges**: whois (netname / descr / OrgName) is authoritative for IP ownership. Never assert from guesswork
8. **Absence of a signature is not evidence of absence**: headers can be removed by reverse proxies and security products
9. **Edge IPs change**: geo-distributed CDN IPs change with each request. Observe multiple times to see the trend
10. **Big players use their own signatures**: Google (`server: gws`), Apple (`server: Apple`) return their own names. Whether they combine downstream CDNs may be unreadable from headers
11. **Resolver matters**: the same name can return different answers via system-default vs 1.1.1.1 vs 8.8.8.8 (cache / ECS / filtering). Always record `@resolver`.
12. **Route 53 Alias hides CNAME**: apex ALIAS records return direct A records. Absence of CNAME is not evidence of no CDN.
13. **Private names are invisible from outside**: private hosted zones and VPC Lattice names only resolve from associated VPCs. Do not conclude absence from public dig.

## Worked example (real observation, target withheld, 2026-11-04)

Field observation of a Japanese SaaS, 2026-11-04 (service name, domains, and exact IPs withheld; observation values unchanged):

| Target | Observation | Conclusion |
|---|---|---|
| Service A — main site (www / apex) | `server: AmazonS3` + `x-amz-cf-id` + `x-amz-cf-pop: KIX56-P4` + `via: 1.1 <hash>.cloudfront.net (CloudFront)` + A 54.239.163.x (no CNAME, direct A record) | S3 + CloudFront |
| Service A — API (`api.<domain>`) | A 35.73.152.x, whois `OrgName: Amazon Technologies Inc.` / `NetName: AT-88-Z`, AS16509 (AMAZON-02) | AWS Tokyo region |
| Service A — marketing site (separate domain) | netname `XSCLD` (Xserver Networks Inc., Osaka), AS131965 | Xserver |

→ Conclusion: the service itself runs on AWS, the marketing site on Xserver (confidence: high). A typical case of "the marketing site is on separate infrastructure".
