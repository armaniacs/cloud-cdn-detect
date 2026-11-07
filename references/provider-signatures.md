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

Example whois of a Tokyo-region IP: `OrgName: Amazon Technologies Inc.` / `NetName: AT-88-Z` / prefix `35.72.0.0/13` / AS16509 (AMAZON-02) ✓

**DNS visibility note**: Route 53 Alias (apex) returns direct A records with no CNAME. Private hosted zone and VPC Lattice names do not resolve from public resolvers. A `dig` result always depends on `@resolver` and where it was run (inside/outside the VPC); record both.

## Google Cloud (GCP)

| Service | HTTP headers | Hostname / DNS | whois / ASN |
|---|---|---|---|
| Cloud Storage (GCS) | `x-guploader-uploadid` ✓, `x-goog-generation` / `x-goog-metageneration` / `x-goog-stored-content-*` / `x-goog-hash` / `x-goog-storage-class` ✓ | `storage.googleapis.com`, `*.storage.googleapis.com`. `x-guploader-*` shows through on custom domains ✓ | AS15169 (GOOGLE) |
| GFE / Cloud Load Balancing (origin side) | When the origin is a GFE (in front of GCLB / GAE / Cloud Run / Firebase Hosting), `via: 1.1 google` comes back even behind a CDN ✓ (observed behind Cloudflare) | | |
| Cloud Functions | | URL format `{region}-{project-id}.cloudfunctions.net` ✓ — the project ID is exposed in the URL (example: `asia-northeast1-example-project.cloudfunctions.net`) | 216.239.x etc., AS15169 |
| Google account avatars | | `lh3.googleusercontent.com` (weak side-evidence of Firebase Auth / Google sign-in) | |

**Pitfall**: Cloudflare Universal SSL edge certificates can be issued by Google Trust Services (`CN=WE1`) or Let's Encrypt. **The CDN edge certificate issuer is not evidence of the origin** (GTS WE1 observed in the wild; use the `via` header and similar for evidence of a Google origin) ✓

**Note**: PaaS platforms such as Vercel / Netlify / Heroku run on AWS. Edge IPs that whois to Amazon do not mean the service uses AWS directly. Prefer CNAMEs and headers.

## CDNs

| Provider | HTTP headers | Hostname / DNS | whois / ASN |
|---|---|---|---|
| Cloudflare | `Server: cloudflare` ✓, `cf-ray` (PoP suffix such as `-KIX`) ✓, `cf-cache-status` | CNAME flattening hides the root CNAME. `*.cloudflare.net` | AS13335 (CLOUDFLARENET) |
| Fastly | `x-served-by: cache-<airport-code>-*` (e.g. `cache-itm1220029-ITM`) ✓, `x-cache: MISS, HIT, MISS` ✓, `x-cache-hits` ✓, `x-timer` ✓ | `*.fastly.net`, `nonssl.global-ssl.fastly.net`, `*.fastlylb.com` | AS54113 (FASTLY) |
| Akamai | `Server: AkamaiGHost` ✓ (observed on www.microsoft.com) | `*.akamaiedge.net`, `*.edgekey.net`, `*.edgesuite.net`, `*.akamaized.net` | AS20940 / AS16625 (AKAMAI) |
| Azure Front Door | `x-azure-ref` | `*.azurefd.net` | AS8075 (MICROSOFT) |
| Azure CDN | | `*.azureedge.net` | AS8075 |

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
