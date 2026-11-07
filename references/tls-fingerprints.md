---
layout: default
title: TLS fingerprints (JA4S)
---

# TLS stack fingerprinting (JA4S) — procedure and registry

The ServerHello parameters (selected cipher suite, extension order, ALPN,
supported groups) depend on the edge's TLS stack (BoringSSL, Quiche,
OpenSSL…), so the stack can be identified **before any HTTP is exchanged** —
even when headers are stripped. JA4S hashes the ServerHello; the JA4S **raw
string** additionally exposes version, cipher count, extension list, and ALPN
in readable form, which makes stack updates trackable.

## Capture procedure (single handshake, passive-equivalent)

This captures only your own handshake to the target — the same traffic an
allowed `openssl s_client` / `curl` makes. Restrict the filter to the target
connection; no broad or promiscuous capture.

```bash
# 1. one-handshake capture (needs capture privilege, e.g. sudo)
sudo tcpdump -i any -w /tmp/hs.pcap 'tcp port 443 and host <target-ip>' &
curl -s -o /dev/null --max-time 10 https://<target>/
kill %1

# 2. compute JA4S (FoxIO-LLC/ja4, python/ja4.py --ja4s -r for the raw string)
python3 ja4.py --ja4s -r /tmp/hs.pcap
```

Ensure a **full handshake**: use a fresh client process per capture (no session
resumption), one capture per target. Delete the pcap after extracting the
fingerprint.

No extra tooling fallback: `openssl s_client -connect <host>:443 -servername
<host> -msg` prints the ServerHello (cipher, extensions, ALPN) for manual
comparison, but prefer the JA4S string when tooling is available.

## Differential protocol (no prefabricated hashes)

JA4S values rotate when providers update stacks, so this repo stores **no
hardcoded hash database**. Instead, compare within the same session:

1. Capture the target's JA4S (`T`).
2. Capture reference endpoints whose provider is known — the provider's own
   site, or the PerRegion/global hostnames from `references/region-codes.md`.
3. `T == reference` corroborates the provider at weight 15 (see scoring in
   `references/provider-signatures.md`). Record both JA4S **strings** (not just
   the hash) in the Evidence table so future stack changes stay diagnosable.

## Registry (direct observation only, ✓ required)

| Provider / stack | JA4S | Raw string | Observed (date) |
|---|---|---|---|
| _none yet — first row must be a same-session target+reference pair_ | | | |

Rules: append only values you captured yourself following the procedure above;
never copy hashes from third-party lists (they rot). If a reference JA4S
changes, keep the old row and append the new one with the new date — the
history is the signal.
