---
layout: default
title: Changelog
---

# Changelog

All notable changes to cloud-cdn-detect are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Dates are JST. Entries under `Unreleased` move to a dated section on commit.

## [Unreleased]

### Added

- Bilingual docs site (EN/JA): `index-ja.md` landing and `CONTRIBUTING-ja.md`
  with EN↔JA switch links. Reference docs (SKILL, signatures, changelog)
  stay English as the source of truth.
- Signatures YAML (Task 10): `references/signatures/SCHEMA.md` (v1, Python+PyYAML,
  provider-per-file), 16 Emerging providers as YAML, `tools/validate-signatures.py`
  (canonical weights, regex compile, boundary negative tests), read-only CI
  (`.github/workflows/validate-signatures.yml`, validates on PR/push, never commits).
- Signatures YAML (Task 11): existing tables migrated (AWS/GCP/Cloudflare/Fastly/
  Akamai/Azure/Vercel/Netlify/GitHub Pages/Heroku/Shopify/Wix/Squarespace/Sakura/
  Xserver/GMO/IIJ), schema v1.1 (`cert` issuer patterns, optional per-signal `verified`).
- Feed watch (Task 12): `tools/feeds.yaml` (13 official/upstream feeds),
  `tools/check-feeds.py` (liveness + freshness + JSON-key checks, one retry on
  transient 5xx), weekly `.github/workflows/feed-watch.yml` (failures filed to a
  single `feed-watch` tracking issue; intake stays human).
- Region / PoP codes: `references/region-codes.md` (Vercel 18 regions verified,
  major IATA hubs, edge-vs-compute semantics); §7 decodes PoP into Evidence,
  pitfall 14 forbids origin-region inference from edge codes.

## [2026-11-07] — DB拡充・多層判定・Pages足場

### Added

- ASN ownership resolution order (`SKILL.md` §5): Cymru DNS TXT as a faster
  complement to Cymru whois, RIPEstat `network-info` / `as-overview`,
  RDAP with APNIC-first fallback (`arin.net` / `db.ripe.net`), JP whois
  fallback with `nkf -w` note. Single-shot free IP APIs (ip-api / ipwho.is /
  IPinfo) documented as cross-check only with rate-limit notes.
- ASN enrichment via PeeringDB (`SKILL.md` §5b): `name` / `aka` / `website` /
  `info_scope` corroboration, empty-`data` handling, level-5 placement.
- Provider-published IP ranges (`SKILL.md` §5c): AWS / Google Cloud / Azure
  Service Tags / Cloudflare / Fastly / GitHub Pages with `jq` filters,
  freshness checks (`createDate` / `creationTime` / `changeNumber`), cache
  rules for multi-MB feeds, and accuracy ordering.
- Certificate Transparency via crt.sh (`SKILL.md` §6b, read-only).
- Web cross-check expansion (`SKILL.md` §8): bgp.he.net, MXToolBox, Cloudflare
  Radar, urlscan past results (read-only); key-only DBs (Shodan / Censys /
  VirusTotal / SecurityTrails / ViewDNS / Wappalyzer GUI) as past-data-only
  with on-demand scan / Rescan explicitly forbidden.
- Emerging CDN/WAF signatures (`references/provider-signatures.md`, cdncheck
  `provider.yaml`-derived, verified 2026-11-07): Tencent EdgeOne, Gcore,
  Imperva, Sucuri, ArvanCloud, CDNetworks, Baidu, Huawei, Leaseweb / Qrator /
  F5 et al. Official feed index incl. CloudFront list endpoint and Gcore feed.
- Detection hardening: CNAME boundary rules (Akamai labels, `ns-cache` vs
  `ens-cache`, `x-served-by` shape), rDNS/PTR hints, w4f-adapted weighted
  scoring (`S_total`, 35/25/25/15/10/10/5, thresholds 60/40), Edge / Platform /
  Origin three-slot reporting, and opt-in probe prohibitions (Akamai `Pragma`,
  WAF error induction, on-demand scans).
- Recursive CNAME-chain expansion and per-IP PTR reversal in `SKILL.md` §3;
  four-layer match pipeline (network / DNS / transport / app) in §7; report
  template and confidence definitions score-mapped in §9.
- GitHub Pages docs (`_config.yml`, `index.md`, `CONTRIBUTING.md`; Jekyll
  front matter on browsable pages) for external contributors.

### Changed

- Evidence hierarchy: level 1 now `whois / RDAP / ASN` (RIPEstat as
  RIR-operated corroboration), level 3 lists the six official feeds with
  freshness verification, level 5 lists the third-party DBs above.
- Ground rules: official IP-range feeds and public web info allowed read-only
  (cache large feeds, never loop-fetch, never trigger new scans).
- `README.md` steps table and hierarchy synced with `SKILL.md`.

### Noted

- No machine-readable feed exists (verified 2026-11-07, do not invent URLs):
  Akamai, Vercel, Netlify, Shopify, Sakura / Xserver / GMO / IIJ.
- BGPView API (`api.bgpview.io`) confirmed dead (NXDOMAIN). JPRS offers no
  RDAP for IP/ASN (domain only).

## [2026-11-07] — DNS resolver visibility

- `dig` workflow is resolver-aware: record system-default resolver, then
  compare `@1.1.1.1` / `@8.8.8.8`, always with `@resolver`, timestamp, TTL,
  and CNAME absence per Evidence row.
- Report template aligned to 4 columns (`Observation | Resolver | Result |
  Suggests`).
- AWS signatures gained a DNS visibility note: Route 53 Alias returns direct
  A records, private hosted zone / VPC Lattice names are invisible publicly;
  a `dig` result always depends on `@resolver` and inside/outside-VPC context.
- Research scaffolding added under `docs/` (resolver design spec, plans,
  literature notes, 4-resolver comparison).

## [2026-11-06] — Initial skill

- `SKILL.md`: passive-only investigation workflow, evidence hierarchy, report
  format with confidence definitions, pitfalls, worked example.
- `references/provider-signatures.md`: signature lookup table for AWS, Google
  Cloud, CDNs, PaaS/hosting, and Japanese hosting.
- `README.md`: skills.sh-style docs with install command and badge.
- Docs translated into English; observation targets anonymized by policy.
- `.gitignore`: exclude macOS metadata (`.DS_Store`, editor swap files).

## [2026-11-04] — Signature database (field investigations)

- Initial table built from a field investigation of a third-party service
  (target withheld) plus direct observation of major providers (Cloudflare /
  Fastly / Vercel / Netlify / Microsoft / Google / GitHub / Wix /
  Squarespace / Shopify / Apple / Sakura Internet / Xserver).
- GFE `via: 1.1 google` and GCS `x-guploader-*` / `x-goog-*` signatures;
  Cloud Functions URL format; Cloudflare edge-issuer caveat (GTS WE1).
- Sakura Cloud ELB (`via: 1.1 sac-elb`, `sac-elb-session`) and Sakura Web
  Accelerator (`x-webaccel-*` / `*.user.webaccel.jp`) signatures.
