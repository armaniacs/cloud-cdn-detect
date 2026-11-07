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
   - Official provider IP-range feeds and public web information (read-only; cache multi-MB feeds, never loop-fetch; never trigger new scans on urlscan/Shodan-type services)
2. **Forbidden**: port scanning, directory discovery, requests that exploit vulnerabilities, high volumes of requests in a short time. Only with explicit permission from the target, and only within the instructed scope.
3. **Separate observation from inference.** Facts (raw header / DNS / whois output) and interpretations ("concluded CloudFront") must correspond in the report; never state conclusions without evidence.
4. Always note that conclusions are technical estimates, not official statements by the provider.

## Evidence hierarchy

1. **whois / RDAP / ASN** — registered owner of the IP. Nearly conclusive. RDAP has the same authority as whois; RIPEstat `as-overview` is RIR-operated corroboration at the same level
2. **HTTP headers / CNAME / TLS certificates** — implementation-derived signatures. Strong but can be rewritten or stripped
3. Provider-published IP ranges (AWS, Google Cloud, Azure Service Tags, Cloudflare, Fastly, GitHub Pages — see §5c). No signatures here: all are unsigned HTTPS JSON/text; verify freshness via `createDate` / `creationTime` / `changeNumber`
4. Public statements on the web (official blogs, case studies, job postings)
5. Third-party databases (PeeringDB, crt.sh, urlscan past results, MXToolBox, Cloudflare Radar, bgp.he.net for ASN-to-org enrichment; Wappalyzer / BuiltWith / Netcraft — indicative only)

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
- Expand the full CNAME chain recursively — intermediaries can reveal the CDN when the final A looks generic (`origin.example.com.cdn.cloudflare.net`). Evaluate every hostname in the chain against the boundary rules in `references/provider-signatures.md` (label boundaries, never substrings)
- Reverse every observed A/AAAA: `dig +short -x <ip> @1.1.1.1`. PTR is auxiliary (weight 10) but can separate layers (`ec2-*.compute` = generic EC2 vs `server-*.r.cloudfront.net` = CloudFront node)

### 4. whois (IP ownership)
```bash
whois <ip> | grep -iE "orgname|netname|descr|owner"
```
- macOS `whois` follows referrals across registries automatically. Don't confuse ARIN referral records (`OrgName: Asia Pacific Network Information Centre` etc.) with actual data
- `owner` can hit ARIN comment lines ("correct owner of the IP address") — skip them

### 5. ASN (IP → AS, no key needed)

Primary order — stop at the first that answers IP ownership:

```bash
whois -h whois.cymru.com " -v <ip>"    # IP → AS (verbose, includes BGP prefix and registry)
whois -h whois.cymru.com AS<number>    # AS → organization
```
Comma-separated multiple lookups and piped bulk queries do not work with macOS `whois`. Run them one at a time.

```bash
nslookup -type=TXT <reversed-ip>.origin.asn.cymru.com   # same Cymru data over DNS, faster
# e.g. 1.1.1.1 → 1.1.1.1.origin.asn.cymru.com returns "13335 | 1.1.1.0/24 | ..."
```

```bash
curl -s 'https://stat.ripe.net/data/network-info/data.json?resource=<ip>'      # prefix + ASN
curl -s 'https://stat.ripe.net/data/as-overview/data.json?resource=AS<number>' # holder (prefer over announced-prefixes: faster, cached)
```

```bash
curl -s https://rdap.apnic.net/autnum/<number>   # JP first (Sakura AS9370, Xserver AS131965, GMO AS7506, IIJ AS2497 are APNIC)
# empty/redirect → try RDAP at arin.net / db.ripe.net in turn; follow a redirect at most once
curl -s https://rdap.apnic.net/ip/<ip>           # IP → managing org (decisive for JP-managed addresses)
```

- JP fallback only: `whois -h whois.apnic.net AS<number>` (`aut-num`/`as-name`/`descr`), then `whois -h whois.nic.ad.jp "AS <number>"` piped through `nkf -w` (JPNIC output is ISO-2022-JP with escape sequences; `grep -a` required)
- Single-shot cross-checks only, never loops (rate-limited): `curl -s 'http://ip-api.com/json/<ip>?fields=status,country,org,as,asname,isp,query'` (free 45 req/min, HTTP only, attribution required), `curl -s https://ipwho.is/<ip>` (read `connection.asn` number only — `connection.org` text is misleading), `https://ipinfo.io/<ip>?token=$IPINFO_TOKEN` (full data only with token)
- Do not use BGPView API (`api.bgpview.io` — confirmed dead, NXDOMAIN as of 2026-11-07). JPRS RDAP does not exist for IP/ASN (domain only) — use JPNIC for IP/AS.

### 5b. ASN enrichment (PeeringDB, optional)

IP → ASN resolution stays in §5 (Team Cymru). Use PeeringDB only to enrich an already-resolved ASN with the operator's self-reported name:

```bash
curl -s "https://www.peeringdb.com/api/net?asn=<number>"
```

- Read `name` / `aka` / `website` / `info_scope`. An `aka` matching the whois netname (e.g. AS7506 `aka` includes `INTERQ`) is strong corroboration
- Empty `data: []` means "not registered in PeeringDB", not "ASN does not exist" — fall back to Cymru + whois only
- Evidence hierarchy level 5 (third-party DB). Never overrides whois/ASN
- A few lookups per investigation only; unauthenticated API, no key needed. Do not use `ix_count` / `fac_count` as provider evidence

### 5c. Provider-published IP ranges (official feeds, hierarchy level 3)

No signatures here — verify freshness (`createDate` / `creationTime` / `changeNumber` is today's or this week's), not signatures. Cache large feeds; never fetch in a loop.

```bash
# AWS (2.75MB, daily) — cache to /tmp
curl -s https://ip-ranges.amazonaws.com/ip-ranges.json -o /tmp/aws.json
jq -r '.prefixes[] | select(.service=="CLOUDFRONT") | .ip_prefix' /tmp/aws.json
# GCP (118KB) — whole-cloud match only, no edge-only tag
curl -s https://www.gstatic.com/ipranges/cloud.json | jq -r '.prefixes[] | select(.ipv4Prefix!=null) | .ipv4Prefix'
# Azure (4.6MB, weekly) — resolve this week's URL from the download page (id=56519), then cache
jq -r '.values[] | select(.name=="AzureFrontDoor.Frontend") | .properties.addressPrefixes[]' /tmp/azure.json
# Cloudflare + Fastly (under 1KB total) — safe to fetch every time
curl -s https://www.cloudflare.com/ips-v4; curl -s https://www.cloudflare.com/ips-v6
curl -s https://api.fastly.com/public-ip-list | jq -r '.addresses[], .ipv6_addresses[]'
# GitHub Pages only (10 prefixes incl. 185.199.108-111.153)
curl -s https://api.github.com/meta | jq -r '.pages[]'
```

- Accuracy: Cloudflare = Fastly (exact edge list) > AWS CloudFront / Azure FrontDoor (per-service tags) > GCP (whole-cloud match) > no-feed providers (below)
- No machine-readable feed exists (verified 2026-11-07, do not invent URLs): Akamai, Vercel (dynamic IPs; use `76.76.21.21` / `cname.vercel-dns.com`), Netlify (apex LB `75.2.60.5` + DNS), Shopify, Sakura / Xserver / GMO / IIJ. For these, judge by DNS + CNAME + ASN/whois + certificates only.

### 6. TLS certificate (optional)
```bash
echo | openssl s_client -connect <host>:443 -servername <host> 2>/dev/null \
  | openssl x509 -noout -subject -issuer
```
- SAN can contain the CDN provider's domain (`*.cloudfront.net` etc.)
- The issuer is a clue too: `Amazon RSA 2048 M01` (AWS ACM), Google Trust Services, Let's Encrypt, etc.

### 6b. Certificate Transparency (crt.sh, read-only)

```bash
curl -s "https://crt.sh/?q=%25.<domain>&output=json" | jq -r '.[].issuer_name' | sort | uniq -c
```
- Corroborate the issuer against §6 (e.g. Cloudflare / Amazon / Google Trust Services). Retry once on transient 502.

### 7. Match signatures

Run four layers in parallel, then score — do not stop at the first header hit:

1. **Network**: every A/AAAA against §5c feeds (Radix/CIDR match, weight 35) + ASN/whois (§4–§5)
2. **DNS**: every CNAME in the expanded chain against provider domains (weight 25, boundary rules apply)
3. **Transport**: certificate SAN/issuer (§6–§6b, weight 25) + TLS stack fingerprint when available (JA4S/JA3S from the normal handshake, weight 15)
4. **Application**: diagnostic headers (weight 10) + PTR (weight 10) + provider cookies (weight 5)

Score with `S_total = min(100, Σ w_i)` (weights table in `references/provider-signatures.md`). Decode PoP/region codes with `references/region-codes.md` and record the edge/compute location in Evidence — edge codes (CloudFront PoP, `cf-ray` suffix, `x-served-by`) locate the serving edge only; only compute-region signals (`x-vercel-id`, `server-timing` backend hints) locate the workload. Compare against `references/provider-signatures.md`. **When a signature not in the table appears, verify its origin via web search before appending it to that file** (this skill is designed to grow with every observation). Never append a signature with an unconfirmed origin, and never record the service you observed it on — append the signature and its technical source (official documentation etc.) only, so third-party target names stay out of this repository. Opt-in probes (Akamai `Pragma`, WAF error induction, on-demand scans) stay forbidden by default — see the signatures file.

### 8. Cross-check on the web
- Provider side: case studies / press releases from AWS / Google Cloud / Azure / Cloudflare etc.
- Operator side: official blogs, engineering blogs (Zenn / Qiita / Hatena), engineer job postings
- Third party (read-only, hierarchy level 5): bgp.he.net (`curl https://bgp.he.net/AS<number>`), MXToolBox (`curl -s "https://mxtoolbox.com/api/v1/lookup/dns/<domain>"`), Cloudflare Radar (`radar.cloudflare.com/domains/domain/<domain>`, browser only — curl 403s), urlscan.io (`api/v1/search/?q=domain:<domain>` then read the result page in a browser for IP/ASN/cert/headers)
- Key holders only (past data, never trigger new scans): Shodan / Censys / VirusTotal / SecurityTrails / ViewDNS / Wappalyzer GUI. `shodan/scan`, urlscan Rescan, and any on-demand scan call are forbidden — they are active scanning, not passive observation
- Example queries: `"<domain>" AWS`, `"<company>" case study cloud`, `"<company>" engineer hiring AWS`, `"<社名>" 導入事例 クラウド`

### 9. Report
```markdown
## Conclusion
Edge: <CDN/WAF> / Platform: <PaaS or n/a> / Origin: <IaaS/hosting or unknown>
(score S_total, confidence: high/medium/low)

## Evidence
| Observation | Resolver | Result | Suggests |
|---|---|---|---|
| HTTP header | system-default | x-amz-cf-id: … | Edge: AWS CloudFront (+10) |
| DNS | @1.1.1.1 | A 54.239.163.x | Edge: CloudFront (+35 feed) |
| whois | system-default | OrgName: Amazon Technologies Inc. | Origin: AWS |

## Caveats
- … (CDN confirmed but origin unidentified, marketing site on a different provider, etc.)
```

**Confidence definitions (score-mapped)**
- **High (Definitive, S_total ≥ 60)**: multiple independent high-weight signals agree — whois/ASN plus headers/CNAME etc., no contradictions
- **Medium (Probable, 40–59)**: signals agree but come from a single source, or public confirmation is missing or outdated
- **Low (Heuristic, < 40)**: weak clues, contradictions, or limited observation scope. A lone header/cookie never exceeds Heuristic

## Pitfalls

1. **CDN ≠ origin**: the origin server behind CloudFront / Cloudflare is essentially invisible from outside. Report the Edge slot as confirmed and leave Origin unknown rather than guessing
2. **Marketing sites are separate**: even under the same operator, corporate/marketing sites and the service itself often run on different infrastructure
3. **PaaS sits on top of a cloud**: whois for Vercel / Netlify / Heroku edge IPs returns Amazon etc. That does not mean "uses AWS directly". Fill Platform (CNAME / `x-vercel-id` / `server-timing`) separately from Origin (ASN/whois)
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
14. **Edge PoP ≠ origin region**: `NRT` in `x-amz-cf-pop`/`cf-ray` means a Tokyo edge served the response (it follows the viewer). Region conclusions need compute signals (`x-vercel-id: hnd1` etc.) or prefix evidence — see `references/region-codes.md`.

## Worked example (real observation, target withheld, 2026-11-04)

Field observation of a Japanese SaaS, 2026-11-04 (service name, domains, and exact IPs withheld; observation values unchanged):

| Target | Observation | Conclusion |
|---|---|---|
| Service A — main site (www / apex) | `server: AmazonS3` + `x-amz-cf-id` + `x-amz-cf-pop: KIX56-P4` + `via: 1.1 <hash>.cloudfront.net (CloudFront)` + A 54.239.163.x (no CNAME, direct A record) | S3 + CloudFront |
| Service A — API (`api.<domain>`) | A 35.73.152.x, whois `OrgName: Amazon Technologies Inc.` / `NetName: AT-88-Z`, AS16509 (AMAZON-02) | AWS Tokyo region |
| Service A — marketing site (separate domain) | netname `XSCLD` (Xserver Networks Inc., Osaka), AS131965 | Xserver |

→ Conclusion: the service itself runs on AWS, the marketing site on Xserver (confidence: high). A typical case of "the marketing site is on separate infrastructure".
