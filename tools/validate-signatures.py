#!/usr/bin/env python3
"""Validate references/signatures/*.yaml against SCHEMA.md (v1). Read-only."""

import ipaddress
import re
import sys
from pathlib import Path

CANONICAL_WEIGHTS = {
    "cidr": 35, "asn": 35, "cname": 25, "cert": 25,
    "tls": 15, "header": 10, "ptr": 10, "cookie": 5,
}
PATTERN_TYPES = {"cname", "header", "cookie", "ptr"}

errors: list[str] = []


def fail(msg: str) -> None:
    errors.append(msg)


def check_signal(doc: dict, sig: dict, i: int, fname: str) -> None:
    loc = f"{fname} signals[{i}]"
    stype = sig.get("type")
    if stype not in CANONICAL_WEIGHTS:
        fail(f"{loc}: unknown type {stype!r}")
        return
    if sig.get("weight") != CANONICAL_WEIGHTS[stype]:
        fail(f"{loc}: weight {sig.get('weight')!r} != canonical {CANONICAL_WEIGHTS[stype]} for {stype}")
    if not sig.get("source"):
        fail(f"{loc}: missing source")
    if stype == "cidr":
        keys = [k for k in ("value", "values", "ref") if sig.get(k)]
        if len(keys) != 1:
            fail(f"{loc}: cidr needs exactly one of value/values/ref, got {keys}")
        for v in ([sig["value"]] if "value" in sig else sig.get("values", [])):
            try:
                ipaddress.ip_network(v, strict=False)
            except ValueError:
                fail(f"{loc}: invalid CIDR {v!r}")
    elif stype == "asn":
        for v in sig.get("values", []):
            if not re.fullmatch(r"AS\d+", str(v)):
                fail(f"{loc}: invalid ASN {v!r}")
        if not sig.get("values"):
            fail(f"{loc}: asn needs values")
    elif stype in PATTERN_TYPES:
        pat = sig.get("pattern")
        if not pat:
            fail(f"{loc}: {stype} needs pattern")
            return
        try:
            rx = re.compile(pat)
        except re.error as e:
            fail(f"{loc}: bad regex {pat!r}: {e}")
            return
        for neg in sig.get("negative", []):
            if rx.search(neg):
                fail(f"{loc}: pattern {pat!r} wrongly matches {neg!r}")
    if stype in ("header", "cookie") and not sig.get("match"):
        fail(f"{loc}: {stype} needs match (header/cookie name)")


def main() -> int:
    try:
        import yaml
    except ImportError:
        print("PyYAML required: pip install pyyaml", file=sys.stderr)
        return 2
    root = Path(__file__).resolve().parent.parent / "references" / "signatures"
    files = sorted(p for p in root.glob("*.yaml"))
    if not files:
        fail("no provider YAML files found")
    for path in files:
        try:
            doc = yaml.safe_load(path.read_text())
        except Exception as e:  # noqa: BLE001
            fail(f"{path.name}: YAML parse error: {e}")
            continue
        for field in ("provider", "display", "verified", "sources", "signals"):
            if field not in doc:
                fail(f"{path.name}: missing field {field!r}")
        if doc.get("provider") != path.stem:
            fail(f"{path.name}: provider slug {doc.get('provider')!r} != filename")
        if not isinstance(doc.get("sources"), list) or not doc.get("sources"):
            fail(f"{path.name}: sources must be a non-empty list")
        sigs = doc.get("signals", [])
        if not isinstance(sigs, list) or not sigs:
            fail(f"{path.name}: signals must be a non-empty list")
        else:
            for i, sig in enumerate(sigs):
                check_signal(doc, sig, i, path.name)
    if errors:
        print(f"{len(errors)} error(s):")
        for e in errors:
            print(f"  - {e}")
        return 1
    print(f"OK: {len(files)} provider files valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
