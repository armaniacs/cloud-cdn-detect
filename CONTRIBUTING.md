---
layout: default
title: Contributing
---

# Contributing to cloud-cdn-detect

External contributions are welcome — especially new provider signatures and
corrections backed by observed evidence.

## Add a signature

1. Verify its origin via web search (official docs preferred) before proposing it.
2. Append it to `references/provider-signatures.md` with its technical source
   (docs URL, feed URL). Never record the third-party service you observed it on.
3. Mark it `✓` only if you directly observed it in the wild.
4. CNAME patterns must use label boundaries, never substrings
   (see "CNAME boundary rules" in the signatures file).

Checklist for the PR:

- [ ] Origin verified (link included, not just asserted)
- [ ] No customer / target names in the diff
- [ ] `CHANGELOG.md` Unreleased entry added

## Other ways to help

- Review the [signature schema design](./docs/superpowers/specs/2026-11-07-signature-schema-design.html)
  and the [help-wanted draft](./docs/research/issues/issue-signature-schema-draft.html) if you run the
  relevant infrastructure.
- Report a wrong inference with the evidence table attached — redacted outputs only.

## Constraints

- Passive observation only. Never submit data obtained from port scans,
  vulnerability probing, on-demand scans, or high-volume requests.
- Do NOT create paid resources to verify something. Verify only what you
  already operate.
