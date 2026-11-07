---
layout: default
title: Region and PoP codes
---

# Region / PoP code reference (cloud-cdn-detect)

PoP and region codes in headers tell **where the response came from**, not
where the origin lives. Decode them with this table, record the edge location
in Evidence, and never infer the origin region from an edge code alone.

## Code semantics per header (edge vs compute)

| Header | Code shape | Meaning |
|---|---|---|
| CloudFront `x-amz-cf-pop` (`KIX56-P4`) | IATA + digits + suffix | **Edge** location that served the response |
| Cloudflare `cf-ray` suffix (`-KIX`, `-NRT`) | `-IATA` | **Edge** colo that served the response |
| Fastly `x-served-by: cache-<host>-IATA` | trailing IATA | **Edge** node that served the response |
| Netlify `server-timing: dc;desc="aws-nrt"` | `aws-<iata>` | AWS-backed **compute/edge** region hint |
| Vercel `x-vercel-id: <region>::…` (`kix1::…`) | Vercel region code | **Compute** region that ran the function — the only code that locates the workload itself |

## Vercel region codes (verified against docs 2026-11-08)

| Code | City | AWS region |
|---|---|---|
| hnd1 | Tokyo | ap-northeast-1 |
| kix1 | Osaka | ap-northeast-3 |
| iad1 | N. Virginia (Washington DC) | us-east-1 |
| sfo1 | San Francisco | us-west-1 |
| pdx1 | Oregon (Portland) | us-west-2 |
| cle1 | Ohio (Cleveland) | us-east-2 |
| fra1 | Frankfurt | eu-central-1 |
| dub1 | Ireland (Dublin) | eu-west-1 |
| lhr1 | London | eu-west-2 |
| cdg1 | Paris | eu-west-3 |
| arn1 | Stockholm | eu-north-1 |
| sin1 | Singapore | ap-southeast-1 |
| syd1 | Sydney | ap-southeast-2 |
| hkg1 | Hong Kong | ap-east-1 |
| bom1 | Mumbai | ap-south-1 |
| icn1 | Seoul | ap-northeast-2 |
| gru1 | São Paulo | sa-east-1 |
| yul1 | Montreal | ca-central-1 |

Vercel runs on AWS; the code names the cloud region hosting the compute.

## GCP region names (verified against docs 2026-11-08)

GCP has no PoP-code header, but region slugs leak through hostnames —
Cloud Run `{service}-{hash}-{region}.a.run.app` and Cloud Functions
`{region}-{project}.cloudfunctions.net`. The slug is a **compute** signal.

| Slug | City |
|---|---|
| asia-northeast1 | Tokyo |
| asia-northeast2 | Osaka |
| asia-northeast3 | Seoul |
| asia-east1 | Taiwan |
| asia-east2 | Hong Kong |
| asia-southeast1 | Singapore |
| asia-southeast2 | Jakarta |
| asia-south1 | Mumbai |
| australia-southeast1 | Sydney |
| us-central1 | Iowa |
| us-east1 | South Carolina |
| us-east4 | N. Virginia |
| us-west1 | Oregon |
| northamerica-northeast1 | Montreal |
| northamerica-northeast2 | Toronto |
| europe-west1 | Belgium |
| europe-west2 | London |
| europe-west3 | Frankfurt |
| europe-west6 | Zurich |
| europe-north1 | Finland |
| southamerica-east1 | São Paulo |
| me-west1 | Tel Aviv |
| africa-south1 | Johannesburg |

Full list: Cloud locations docs. New regions appear yearly — look up, don't guess.

## Azure region names (verified against docs 2026-11-08)

Region slugs leak through classic hostnames —
`{name}.{region}.cloudapp.azure.com` (`*.azurewebsites.net` carries no region).
The slug is a **compute** signal.

| Slug | City |
|---|---|
| japaneast | Tokyo (Saitama) |
| japanwest | Osaka |
| eastasia | Hong Kong |
| southeastasia | Singapore |
| australiaeast | Sydney |
| centralindia | Pune |
| eastus / eastus2 | Virginia |
| westus2 | Washington state |
| centralus | Iowa |
| uksouth | London |
| westeurope | Netherlands |
| northeurope | Ireland |
| francecentral | Paris |
| germanywestcentral | Frankfurt |
| swedencentral | Gävle |
| switzerlandnorth | Zurich |
| canadacentral | Toronto |
| brazilsouth | São Paulo |
| uaenorth | UAE |

`x-azure-ref` is opaque — do not parse region out of it.

## Cloudflare / Fastly need no separate table

Both use the same IATA system as the edge table above (`cf-ray: …-NRT`,
`x-served-by: cache-…-ITM`). All such codes are **edge-only**.

## Sakura Cloud zones (verified against SDK source 2026-11-08)

Zone slugs from [sacloud/libsacloud `types/zone.go`](https://github.com/sacloud/libsacloud/blob/main/v2/sacloud/types/zone.go).
A zone names the datacenter itself, so it is a **compute** signal (like a
Vercel region code, not an edge PoP).

| Slug | Zone |
|---|---|
| tk1a | 東京第1ゾーン |
| tk1b | 東京第2ゾーン |
| is1a | 石狩第1ゾーン |
| is1b | 石狩第2ゾーン (SDKコメント原文は「第1」のまま・ID 31002) |
| tk1v | サンドボックスゾーン |

Where slugs surface: Sakura Cloud API endpoint hostnames
(`…/cloud/zone/{tk1a,…}/api/…`), usacloud/Terraform `--zone` values, and
proxy configs. Host `svXX-oskXX-jp` in Web Accelerator `via` lines reads as
Osaka (`osk` ≈ metro code; IATA airports are KIX/ITM) — treat as an Osaka
edge hint, corroborated by CNAME/ASN as usual.

## Major IATA codes for edge headers (CloudFront / Cloudflare / Fastly)

Same IATA system as above. Frequently observed hubs:

| Code | City | Nearby cloud region |
|---|---|---|
| NRT / HND | Tokyo (Narita / Haneda) | ap-northeast-1 |
| KIX / ITM | Osaka (Kansai / Itami) | ap-northeast-3 |
| IAD | N. Virginia (Dulles) | us-east-1 |
| SFO / SJC | San Francisco / San Jose | us-west-1 |
| LAX | Los Angeles | us-west-1 |
| PDX | Oregon (Portland) | us-west-2 |
| DFW | Texas (Dallas) | us-east-1 / us-west-2 reach |
| ORD | Chicago | us-east-2 reach |
| FRA | Frankfurt | eu-central-1 |
| LHR | London | eu-west-2 |
| CDG | Paris | eu-west-3 |
| DUB | Dublin | eu-west-1 |
| SIN | Singapore | ap-southeast-1 |
| SYD | Sydney | ap-southeast-2 |
| ICN | Seoul | ap-northeast-2 |
| HKG | Hong Kong | ap-east-1 |
| BOM | Mumbai | ap-south-1 |
| JFK | New York | us-east-1 |
| ATL | Atlanta | us-east-1 |
| AMS | Amsterdam | westeurope |
| HEL | Helsinki | eu-north-1 (nearest) |
| MAA | Chennai | ap-south-1 (nearest) |
| HIO | Hillsboro (Portland metro) | us-west-2 |

Any other 3-letter code: look it up as an IATA airport code. Codes name the
**serving edge**, which follows the viewer — a Tokyo viewer hitting a US-only
service still gets `NRT`. Edge location is evidence of CDN usage, not of the
origin's region.

## Rules

- Record the decoded edge/compute location in the Evidence table
  (e.g. `x-amz-cf-pop: NRT57-C1 → Edge: Tokyo`).
- Region-level conclusions (e.g. "runs in ap-northeast-1") require a
  **compute-region** signal (`x-vercel-id`, `server-timing` backend hint) or
  whois prefix evidence — never an edge PoP alone.
- Unknown codes: search the provider's edge-location / region docs before
  adding them here; never guess from resemblance.
- Leaked AWS-internal hostnames decode as compute signals with standard slugs:
  `internal-*.{region}.elb.amazonaws.com`, `ip-10-0-x-x.{region}.compute.internal`
  (the latter is the documented EC2 VPC-origin domain format).
- Lambda Web Functions: the PerRegion hostname embeds the serving region
  (`{id}.r8m.lambda-web.{region}.on.aws`) — a **compute** signal. The global
  hostname (`{id}.lambda-web.global.on.aws`) resolves to different PerRegion
  CNAMEs per viewer location (latency routing), so always record where and
  via which resolver you resolved it.
