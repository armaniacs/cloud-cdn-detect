---
layout: default
title: Provider signatures
---

# Provider signature reference (cloud-cdn-detect)

Match observed HTTP headers, DNS records, whois results, and TLS certificates against this table to identify the provider.

## Operating rules

- Confidence is "high" only when multiple independent signatures agree. A single signature is "medium" or below
- For IP ownership, whois (netname / descr / OrgName) and ASN are authoritative. Headers can be rewritten or removed
- ✓ = verified by direct observation. No mark = established knowledge (lower certainty; verify again when it matters)
- **When a signature not in this table appears**: confirm its origin via web search, then append it to this file. Never append a signature with an unconfirmed origin
- **Do not record observation targets**: append signatures with their technical source (official documentation etc.), not the third-party service you observed them on

## AWS

| Service | HTTP headers | Hostname / DNS | whois / ASN |
|---|---|---|---|
| CloudFront | `x-amz-cf-id` ✓, `x-amz-cf-pop` (PoP code, e.g. `KIX56-P4`) ✓, `via: 1.1 <hash>.cloudfront.net (CloudFront)` ✓, `x-cache: Hit/Miss/Redirect/Error from cloudfront` ✓, `Server: CloudFront` on redirects ✓ | CNAME `d*.cloudfront.net`. The root may show no CNAME and point to direct A records ✓ | Edge IPs fall inside AS16509 (AMAZON-02) |
| S3 static hosting | `Server: AmazonS3` ✓, `x-amz-server-side-encryption: AES256` ✓ | `*.s3-website-<region>.amazonaws.com` | `Server: AmazonS3` also shows through when it sits behind CloudFront as the origin ✓ |
| API Gateway | `x-amzn-RequestId`, `x-amzn-ErrorType` | `*.execute-api.<region>.amazonaws.com` | |
| ELB / ALB | `Server: awselb` | `dualstack.*.elb.amazonaws.com` | |
| ACM-issued certificates | Certificate issuer: `Amazon RSA 2048 M01` ✓ etc. | | |
| Lambda Web Functions (GA Oct 2026) | Platform injects `lambda-web-request-id` into the request (visible in responses only if the app echoes it); `X-Forwarded-For` present | Global URL `{id}.lambda-web.global.on.aws` → latency-routed CNAME `{id}.r8m.lambda-web.{region}.on.aws` (PerRegion URL) → `c300.{region}.prod.frontend.lambda-lite.aws.dev` → A. The CNAME chain differs by resolver location — compare `@1.1.1.1` vs `@8.8.8.8` and record where you resolved from | Frontend IPs whois to Amazon (AS16509). Regions observed: ap-northeast-1, us-east-1, us-east-2, us-west-2, eu-west-1, eu-central-1 |

Example whois of a Tokyo-region IP: `OrgName: Amazon Technologies Inc.` / `NetName: AT-88-Z` / prefix `35.72.0.0/13` / AS16509 (AMAZON-02) ✓

**VPC origins (Nov 2024)**: ALB/NLB/EC2 in private subnets can serve as CloudFront origins over a private ENI connection. Consequences for passive observation:
- No edge signature change — `x-amz-cf-*`, `via`, `x-cache` look identical. There is no header/CNAME/ASN test that distinguishes a VPC origin from a public one.
- The origin is unresolvable and unreachable from outside by design ("won't be discoverable over the internet" after the subnet goes private). Report Origin as "private VPC (type unknown)" at most; never guess ALB vs NLB vs EC2.
- Leak signals (only if they surface in cert SAN / headers / error pages): `internal-*.{region}.elb.amazonaws.com` (internal LB hostname; region slug decodes via `references/region-codes.md` rules) and EC2 private DNS `ip-10-0-x-x.{region}.compute.internal` (documented as the EC2 VPC-origin domain format). Either is a strong VPC-origin hint (weight as CNAME, 25).
- Background knowledge (not observable): origins allow the `com.amazonaws.global.cloudfront.origin-facing` managed prefix list or the service SG `CloudFront-VPCOrigins-Service-SG`. Supported in Tokyo (`ap-northeast-1`, except `apne1-az3`) and Osaka (`ap-northeast-3`).

**DNS visibility note**: Route 53 Alias (apex) returns direct A records with no CNAME. Private hosted zone and VPC Lattice names do not resolve from public resolvers. A `dig` result always depends on `@resolver` and where it was run (inside/outside the VPC); record both.

## Google Cloud (GCP)

| Service | HTTP headers | Hostname / DNS | whois / ASN |
|---|---|---|---|
| Cloud Storage (GCS) | `x-guploader-uploadid` ✓, `x-goog-generation` / `x-goog-metageneration` / `x-goog-stored-content-*` / `x-goog-hash` / `x-goog-storage-class` ✓ | `storage.googleapis.com`, `*.storage.googleapis.com`. `x-guploader-*` shows through on custom domains ✓ | AS15169 (GOOGLE) |
| GFE / Cloud Load Balancing (origin side) | When the origin is a GFE (in front of GCLB / GAE / Cloud Run / Firebase Hosting), `via: 1.1 google` comes back even behind a CDN ✓ (observed behind Cloudflare) | | |
| Cloud Functions | | URL format `{region}-{project-id}.cloudfunctions.net` ✓ — the project ID is exposed in the URL (example: `asia-northeast1-example-project.cloudfunctions.net`) | 216.239.x etc., AS15169 |
| Cloud Run | | Hostname format `{service}-{hash}-{region}.a.run.app` — `{region}` is a GCP region slug, decode via `references/region-codes.md` | |
| Google account avatars | | `lh3.googleusercontent.com` (weak side-evidence of Firebase Auth / Google sign-in) | |

**Pitfall**: Cloudflare Universal SSL edge certificates can be issued by Google Trust Services (`CN=WE1`) or Let's Encrypt. **The CDN edge certificate issuer is not evidence of the origin** (GTS WE1 observed in the wild; use the `via` header and similar for evidence of a Google origin) ✓

**Note**: PaaS platforms such as Vercel / Netlify / Heroku run on AWS. Edge IPs that whois to Amazon do not mean the service uses AWS directly. Prefer CNAMEs and headers.

## CDNs

| Provider | HTTP headers | Hostname / DNS | whois / ASN |
|---|---|---|---|
| Cloudflare | `Server: cloudflare` ✓, `cf-ray` (PoP suffix such as `-KIX`) ✓, `cf-cache-status`, `cf-mitigated: challenge\|blocked` | CNAME flattening hides the root CNAME. `*.cloudflare.net` | AS13335 (CLOUDFLARENET) |
| Fastly | `x-served-by: cache-<airport-code>-*` (e.g. `cache-itm1220029-ITM`) ✓, `x-cache: MISS, HIT, MISS` ✓, `x-cache-hits` ✓, `x-timer` ✓, `Fastly-Debug-Digest`, `Server: artisan` (some properties, e.g. fastly.com) | `*.fastly.net`, `nonssl.global-ssl.fastly.net`, `*.fastlylb.com` | AS54113 (FASTLY) |
| Akamai | `Server: AkamaiGHost` ✓ (observed on www.microsoft.com), `X-Akamai-Transformed`, `X-Check-Cacheable` | `*.akamaiedge.net` (Standard TLS), `*.edgekey.net` (Enhanced TLS), `*.edgesuite.net`, `*.akamaized.net`, `*.akadns.net`. Never shorten to `akamai.net` — that misses `akamaiedge.net` on dot-boundary | AS20940 / AS16625 (AKAMAI). No official CIDR feed; ASN tracking is the standard |
| Azure Front Door | `x-azure-ref`, `X-MSEdge-Ref` | `*.azurefd.net`, `*.afd.azureedge.net` | AS8075 (MICROSOFT) |
| Azure CDN | `X-Cache: *OriginShield*` | `*.azureedge.net` | AS8075 |
| App Service / Cloud Services | | `{name}.{region}.cloudapp.azure.com` (`{region}` is an Azure slug, decode via `references/region-codes.md`), `*.azurewebsites.net` (no region) | AS8075 |

## Emerging CDN / WAF / regional providers (cdncheck-derived, verify when it matters)

Sourced from [ProjectDiscovery cdncheck `provider.yaml`](https://github.com/projectdiscovery/cdncheck/blob/main/cmd/generate-index/provider.yaml) (verified 2026-11-07). No ✓ mark = established knowledge from that file, not direct observation. Verify again when it matters.

| Provider | HTTP headers / cookies | Hostname / DNS | IP / ASN source |
|---|---|---|---|
| Tencent Cloud EdgeOne | `Server: EO-Edge`, `eo-log-uuid`, `eo-cache-status` | `*.eo.dnse1.com`, `*.edgeone.co` | Static CIDR in `provider.yaml` (`tencent:` block); AS132203 et al. |
| Gcore | `Server: gcore`, `X-GCore-Request-ID` | `*.gcdn.co` | Official feed `https://api.gcore.com/cdn/public-ip-list` (verified 200, ~42KB) |
| Imperva (Incapsula) | `X-Iinfo`, `X-CDN: Imperva`, cookies `incap_ses_*`, `visid_incap_*` | `*.incapdns.net` | Official IP list via API endpoint (see cdncheck sources) |
| Sucuri CloudProxy | `Server: Sucuri/Cloudproxy`, `X-Sucuri-ID`, `X-Sucuri-Cache` | `*.sucuri.net` | Official CIDR incl. `192.88.134.0/23` |
| CDNetworks | Vendor headers vary by property | Apex/edge hostnames per contract | Static CIDR in `provider.yaml` (`cdnetworks:` block) |
| ArvanCloud | Vendor headers vary by property | `*.arvancloud.ir` feed `https://www.arvancloud.ir/fa/ips.txt` | AS208006 / AS205585; static CIDR `185.143.232.0/22`, `185.215.232.0/22` etc. |
| Baidu Cloud CDN | Vendor headers vary by property | Baidu edge hostnames | Static CIDR in `provider.yaml` (`baidu:` block, hundreds of /24) |
| Huawei Cloud CDN | Vendor headers vary by property | Huawei edge hostnames | AS149640 |
| Leaseweb / Qrator / F5 / GoCache / WangSu / KINX / LG / SKB | Vendor-specific | See `provider.yaml` | ASN (`AS60626` Leaseweb; `AS197068`/`AS200449`/`AS51115` Qrator) and static `cidr:` blocks (F5, Qrator, cafe24, gocache, kinx, lgtelecom, skbroadband, huawei, wangsu) |

Do not copy the thousand-line CIDR blocks into this file. Sync from `provider.yaml`
at investigation time instead.

## PaaS / hosting

| Provider | HTTP headers | Hostname / DNS | Notes |
|---|---|---|---|
| Vercel | `Server: Vercel` ✓, `x-vercel-id` (`kix1::…` format) ✓, `x-vercel-cache` ✓ | apex A `76.76.21.21`, `cname.vercel-dns.com`, `*.vercel.app` | Edge runs on AWS |
| Netlify | `Server: Netlify` ✓, `x-nf-request-id` ✓, `server-timing` contains `dc;desc="aws-nrt"` ✓ | `*.netlify.app`, `netlifyglobalcdn.com` | `server-timing` reveals the AWS backend |
| GitHub Pages | `Server: GitHub.com` ✓, `x-github-request-id` ✓, `x-github-edge-region` ✓ | `*.github.io`, A `185.199.108-111.153` | github.com also uses Fastly (`x-served-by: cache-…-ITM` ✓) |
| Heroku | `via: 1.1 vegur` | `*.herokuapp.com`, `*.herokudns.com` | Runs on AWS |
| Shopify | `x-shopid`, `x-shopify-stage` (store pages), `Server: cloudflare` ✓ (www.shopify.com) | `*.myshopify.com` | A typical example of running on top of Cloudflare |
| Wix | `x-wix-request-id` ✓, `Server: Pepyaka` ✓, `via: 1.1 google` ✓ | Wix DNS | `server-timing`'s `dc;desc=fastly_g` reveals Fastly + Google behind ✓ |
| Squarespace | `Server: Squarespace` ✓, `x-contextid` ✓ | Custom domains CNAME to `ext-cdn.squarespace.net` | |

Google family: `Server: gws` ✓ (google.com), `Server: gfe` (Google Front End, across Google-operated services), `via: 1.1 google` ✓ (signature of passing through a GFE; survives behind Cloudflare — verified in the wild), GCS: `x-guploader-uploadid` / `x-goog-generation` / `x-goog-hash` / `x-goog-storage-class` (shows through CDNs — verified in the wild) ✓, other `x-goog-*`. AS15169 (GOOGLE). Apple family: `Server: Apple` ✓ (a rewritten self-signature; whether downstream CDNs are combined cannot be determined from headers).

## Japanese hosting providers

| Provider | HTTP headers | Hostname / DNS | whois / ASN |
|---|---|---|---|
| Sakura Internet | `Server: nginx` (weak signature; rely on whois) ✓ | `*.sakura.ne.jp` | netname `SAKURA` / `SAKURA-NET` ✓, descr `SAKURA Internet Inc.` ✓, AS9370 (SAKURA-B) ✓ |
| Sakura Cloud (Enhanced Load Balancer) | `via: 1.1 sac-elb` ✓ (observed in the wild; appears as the origin ELB in front of the CDN) | Session cookie `sac-elb-session` (documented in the Sakura Cloud manual: https://manual.sakura.ad.jp/cloud/appliance/enhanced-lb/ ) | |
| Sakura Web Accelerator | `x-webaccel-origin-status` ✓, via `ApacheTrafficServer-first/-second` (node names `svXX-oskXX-jp`) ✓ | CNAME `*.user.webaccel.jp` ✓, actual servers `site-*.gslb1.sakura.ne.jp` ✓ | |
| Xserver | `server: nginx` (weak signature) ✓ | `sv*.xserver.jp` | netname `XSCLD` / `XSERVER` ✓, descr `Xserver Networks Inc.` ✓, AS131965 (XSERVER) ✓ |
| GMO group (ConoHa / lolipop / heteml) | | `*.conoha.io`, `*.lolipop.jp`, `*.heteml.net` | AS7506 (GMO Internet), netname `INTERQ` family |
| IIJ | | | AS2497 (IIJ) ✓ |

Sakura Internet and Xserver are both headquartered in Umeda, Osaka (Ofuka-cho), so do not judge by the whois address alone (GRAND FRONT OSAKA = Xserver, GRAND GREEN OSAKA = Sakura Internet, as observed in November 2026).

## Official IP feed index (for §5c; verified 2026-11-07)

| Provider | Feed URL | Notes |
|---|---|---|
| AWS CloudFront | `https://ip-ranges.amazonaws.com/ip-ranges.json` and `https://d7uri8nf7uskq.cloudfront.net/tools/list-cloudfront-ips` (both verified 200) | Filter `service=="CLOUDFRONT"` in the former; the latter is a flat `CLOUDFRONT_GLOBAL_IP_LIST` |
| Google Cloud | `https://www.gstatic.com/ipranges/cloud.json` (118KB) and `https://www.gstatic.com/ipranges/goog.json` (bot/commons split) | Whole-cloud match only; exclude Googlebot via `goog.json` |
| Azure | `ServiceTags_Public_*.json` via download page `id=56519` (weekly, ~4.6MB) | `AzureFrontDoor.Frontend`, `AzureCloud.<region>` tags; cache weekly |
| Cloudflare | `https://www.cloudflare.com/ips-v4`, `/ips-v6` (~334B) | Exact edge list |
| Fastly | `https://api.fastly.com/public-ip-list` (~451B) | Exact edge list |
| Gcore | `https://api.gcore.com/cdn/public-ip-list` (~42KB) | Exact edge list |
| GitHub | `https://api.github.com/meta` (`pages` key, 10 prefixes) | Pages only |
| ArvanCloud | `https://www.arvancloud.ir/fa/ips.txt` | Per cdncheck `provider.yaml` |
| GoCache (Brazil) | `https://gocache.com.br/ips` | Per cdncheck `provider.yaml` |

No machine-readable feed (verified 2026-11-07): Akamai, Vercel, Netlify, Shopify, Sakura / Xserver / GMO / IIJ. Judge by DNS + CNAME + ASN/whois + certificates only.

## CNAME boundary rules (avoid false positives)

Match on DNS-label boundaries, never substrings:

- Akamai: `akamaiedge.net` does NOT contain the label `akamai.net`. A regex for `akamai\.net` misses `akamaiedge.net` entirely. List `akamaiedge.net` / `edgekey.net` / `edgesuite.net` / `akamaized.net` / `akadns.net` explicitly.
- Proxy `Via`: Citrix NetScaler emits `ns-cache`; Alibaba/NetEase emit `ens-cache`. Use `\bns-cache\b`, otherwise every Chinese CDN becomes "Citrix".
- `x-served-by` presence alone is not Fastly: Cloudflare-hosted sites have returned `x-served-by: marketing-site`. Require the `cache-<pop>` value shape, corroborated by CNAME/ASN.

## rDNS / PTR hints (auxiliary, weight 10)

Reverse DNS can be more service-specific than whois. Resolve every observed A/AAAA back:

```bash
dig +short -x <ip> @1.1.1.1
```

- `ec2-*.compute-1.amazonaws.com` = generic EC2; `server-*.fra*.r.cloudfront.net` = CloudFront delivery node. Same owner (Amazon), different layer — record the distinction for the Edge/Platform/Origin split below.

## Weighted scoring (w4f-adapted, for §7)

Add weights of all matching signals, capped at 100:

`S_total = min(100, Σ w_i)`

| Signal | w | Rationale |
|---|---|---|
| Official CIDR match (§5c) | 35 | Anycast/netblock is hardest to fake |
| CNAME to provider domain (with boundary rules) | 25 | Deliberate delegation by the operator |
| Provider CA issuer (ACM / Google Trust / Cloudflare) corroborating TLS SAN | 25 | Management-plane evidence |
| TLS stack fingerprint (JA4S/JA3S, when available) | 15 | Transport-layer corroboration |
| Diagnostic header (`x-amz-cf-id`, `cf-ray`, `x-served-by: cache-*`, …) | 10 | Strong but strippable |
| PTR match | 10 | Auxiliary |
| Provider cookie (`sac-elb-session`, `incap_ses_*`, …) | 5 | Weakest, easily set by others |

Map the total to the report confidence: **≥60 Definitive → high**, **40–59 Probable → medium**, **<40 Heuristic → low**. A single header/cookie alone can never exceed Heuristic. Keep the evidence table row-by-row regardless of the score.

## Multi-layer output: Edge / Platform / Origin

Never collapse a stack to a single winner. Report three slots:

- **Edge** (answers the HTTP request): CDN/WAF — `cf-ray`, Cloudflare IP, `x-amz-cf-id`, Akamai edge hostname…
- **Platform** (runs the app): PaaS — `x-vercel-id`, `server-timing: aws-nrt`, `via: 1.1 google` surviving behind a CDN, `*.vercel-dns.com` CNAME…
- **Origin / Underlying IaaS** (owns the IP): BGP/whois — `OrgName: Amazon Technologies Inc.`, AS16509…

Example: `cf-ray` + Cloudflare IP (Edge: Cloudflare), `x-vercel-id: kix1::…` (Platform: Vercel), AS16509/Amazon whois (Origin: AWS). "Uses Vercel" ≠ "uses AWS directly".

## Opt-in probes (forbidden by default)

Passive operation is the default and the only behavior without explicit target permission. The following are documented for completeness and MUST NOT run unless the target explicitly opts in:

- Akamai `Pragma: akamai-x-cache-on, akamai-x-cache-remote-on, akamai-x-check-cacheable, akamai-x-get-cache-key, akamai-x-get-true-cache-key, akamai-x-get-request-id, akamai-x-serial-no` — reveals `X-Cache: TCP_HIT` / `X-Serial` on Akamai edges.
- WAF error-page fingerprinting (sending malformed input to trigger block pages such as Imperva "incident ID", FortiWeb `cookiesession1`, AWS WAF "Request blocked") — active probing, same prohibition as port scans.
- Any `shodan/scan`-style on-demand scan or urlscan Rescan.

## SaaS (reported separately as services in use, not as "the company's infrastructure")

Zendesk (`support.*`, `static.zdassets.com`), statuspage.io, Stripe, Google speech recognition, reCAPTCHA, etc. When an FAQ or spec text leads to an inference such as "the speech recognition is Google's", state it clearly separated from technical observation (headers / DNS / whois).

## On signature stripping and spoofing

- Reverse proxies and security products can remove `Server` and vendor headers
- `Server` can be rewritten (fastly.com returns the joke `server: Artisanal bits` ✓)
- A missing signature does not mean the provider is not in use

## Changelog

- 2026-11-04: Initial version, built from a field investigation of a third-party service (target withheld) plus direct observation of major providers (Cloudflare / Fastly / Vercel / Netlify / Microsoft / Google / GitHub / Wix / Squarespace / Shopify / Apple / Sakura Internet / Xserver)
- 2026-11-04: Added GFE `via: 1.1 google` and GCS `x-guploader-*` / `x-goog-*` signatures from a smoke test on a third-party site (target withheld)
- 2026-11-04: Added the Google Cloud section from an investigation of a site running on Google Cloud (target withheld): GCS signatures `x-guploader-*` / `x-goog-*`, `via: 1.1 google` on GFE origins, the Cloud Functions URL format, and the caveat that Cloudflare edge certificate issuers are not origin evidence
- 2026-11-04: Added Sakura Cloud ELB (`via: 1.1 sac-elb`, sourced from the Sakura Cloud manual's cookie spec) and Sakura Web Accelerator (`x-webaccel-*` / `*.user.webaccel.jp`) signatures from an investigation of a third-party site (target withheld)
- 2026-11-06: Translated into English for skills.sh
- 2026-11-06: Anonymized — observation targets are no longer recorded in this repository
- 2026-11-07: Added Emerging CDN/WAF section (Tencent EdgeOne, Gcore, Imperva, Sucuri, ArvanCloud, CDNetworks, Baidu, Huawei, Leaseweb/Qrator/F5 et al., sourced from cdncheck provider.yaml), official IP feed index (incl. CloudFront list endpoint and Gcore feed), CNAME boundary rules, rDNS hints, w4f-adapted weighted scoring, Edge/Platform/Origin split, and opt-in probe prohibitions
