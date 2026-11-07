# Signatures YAML schema (v1)

Machine-checkable mirror of the Emerging CDN/WAF section in
`references/provider-signatures.md`. Markdown stays the source of truth
until every provider migrates (hybrid policy).

## File layout

- One file per provider: `references/signatures/<provider-slug>.yaml`
- Slug must equal the filename.

## Top-level fields

| Field | Required | Meaning |
|---|---|---|
| `provider` | yes | slug, must equal filename |
| `display` | yes | human-readable name |
| `verified` | yes | `true` only if directly observed in the wild |
| `sources` | yes | ≥1 URL (official docs preferred, cdncheck `provider.yaml` ok) |
| `signals` | yes | ≥1 signal, see below |

## Signal fields

| Field | Required | Meaning |
|---|---|---|
| `type` | yes | one of `cidr` `cname` `cert` `tls` `header` `ptr` `cookie` `asn` |
| `weight` | yes | canonical weight for the type (see table) |
| `pattern` | for `cname`/`header`/`cookie`/`ptr` | Python regex, label-boundary aware |
| `value` | for `cidr` (inline) | CIDR string, e.g. `192.88.134.0/23` |
| `values` | alternative to `value` | list of inline CIDRs / ASNs (`AS208006`) |
| `ref` | alternative, `cidr` only | bulk pointer, e.g. `cdncheck:cidr:tencent` (full list lives upstream, never copied here) |
| `match` | for `header`/`cookie` | header/cookie name, e.g. `Server`, `incap_ses_*` |
| `source` | yes | URL backing this signal |
| `negative` | recommended for `cname`/`header` | strings the pattern MUST NOT match (boundary tests) |

Canonical weights: `cidr`/`asn` 35, `cname`/`cert` 25, `tls` 15,
`header`/`ptr` 10, `cookie` 5. Score: `S_total = min(100, Σw)`;
≥60 Definitive, 40–59 Probable, <40 Heuristic.

## Validator rules (`tools/validate-signatures.py`)

1. YAML parses; required fields present; slug == filename.
2. `type` in enum; `weight` equals the canonical weight for the type.
3. Every regex compiles; every `negative` entry does NOT match.
4. `cidr` has exactly one of `value`/`values`/`ref`; `cname`/`header`/
   `cookie`/`ptr` have `pattern`; `asn` has `values`.
