---
layout: default
title: Help wanted — signature schema
---

# [Help wanted] Review signature YAML schema + feed auto-follow design

## Why
Detection rules live in Markdown today (`references/provider-signatures.md`).
We want machine-checkable YAML plus weekly auto-follow of upstream feeds
without breaking passive-only operation.

## Repro steps (review only, no infra changes)
1. Read `docs/superpowers/specs/2026-11-07-signature-schema-design.md`.
2. Comment on: field coverage (cidr/cname/cert/tls/header/ptr/cookie),
   boundary-test cases (`akamaiedge.net` vs `akamai.net`,
   `ns-cache` vs `ens-cache`, `x-served-by` shape), weight mapping
   (35/25/25/15/10/10/5 → thresholds 60/40).
3. Flag any feed URL that should NOT be auto-followed (auth-walled, unstable).
   Current candidates: cdncheck `provider.yaml` (`cdn.urls` / `cdn.asn` /
   `cdn.cidr`), CloudFront/Gcore/Fastly/Cloudflare/Google official feeds.

## Constraints
- No new active probing. Read-only fetches of public feeds only.
- Markdown stays source of truth until the validator passes on CI.
- Do NOT create paid resources. Paste redacted outputs only.
