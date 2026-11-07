# [Help wanted] Verify VPC Lattice DNS resolution from inside a VPC

## Why
Public `dig` cannot see Lattice names. We need hands-on verification from an associated VPC.

## Repro steps (for collaborator with a VPC + Lattice service)
1. From an EC2/CloudShell inside the associated VPC: `dig <lattice-service-dns> +short`
2. From outside (public resolver `@1.1.1.1`): `dig <same-name> +short` (expect: no answer / NXDOMAIN)
3. Record: VPC ID, region, resolver used (`169.254.169.253` or VPC CIDR+2), timestamp, outputs.

## Expected
- Inside: service IPs; Outside: no private answer. Confirm and paste both outputs.

## Constraints
- Passive DNS only. Do not publish customer domain names. Redact as needed.
