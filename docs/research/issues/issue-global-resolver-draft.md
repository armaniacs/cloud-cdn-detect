# [Help wanted] Verify Route 53 Global Resolver behavior (reported GA 2026-03, link needed)

## Why
Global Resolver is reported to have gone GA in 2026-03 (announcement link needed — paste it here when posting). It is expensive to run, so maintainers cannot verify alone.

## Repro steps (only if you already run it)
1. Link the AWS What's New / Docs URL for GA (paste URL + date accessed).
2. From an associated VPC: `dig <name> @<global-resolver-endpoint> +short` with timestamp.
3. From public `@1.1.1.1` / `@8.8.8.8`: same name (expect: different or no private answer).

## Cost warning
- Do NOT create paid resources for this issue. Only verify if you already operate Global Resolver. Paste redacted outputs only.
