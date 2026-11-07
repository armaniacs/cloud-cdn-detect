#!/usr/bin/env python3
"""Liveness + freshness check for tools/feeds.yaml. Read-only, low volume.

Exit 0 when every feed answers 200 with a non-empty, fresh-enough payload.
Exit 1 otherwise. Transient 5xx/timeouts get exactly one retry.
"""

import datetime
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

TIMEOUT = 20


def fetch(url: str) -> tuple[int, bytes]:
    last: tuple[int, bytes] = (-1, b"")
    for attempt in (1, 2):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "cloud-cdn-detect-feed-watch/1.0"})
            with urllib.request.urlopen(req, timeout=TIMEOUT) as res:
                return res.status, res.read()
        except Exception as e:  # noqa: BLE001 - any fetch failure is a FAIL
            last = (-1, str(e).encode())
            if attempt == 1:
                time.sleep(10)
    return last


def freshness_ok(payload: bytes, field: str, max_age_days: int) -> tuple[bool, str]:
    try:
        data = json.loads(payload)
        raw = str(data.get(field, ""))
    except Exception:
        return False, "unparseable JSON"
    m = re.search(r"(\d{4}-\d{2}-\d{2})", raw)
    if not m:
        return False, f"no date in {field}={raw!r}"
    age = (datetime.date.today() - datetime.date.fromisoformat(m.group(1))).days
    if age > max_age_days:
        return False, f"{field}={raw} age {age}d > {max_age_days}d"
    return True, f"{field} age {age}d"


def main() -> int:
    try:
        import yaml
    except ImportError:
        print("PyYAML required: pip install pyyaml", file=sys.stderr)
        return 2
    manifest = yaml.safe_load((Path(__file__).parent / "feeds.yaml").read_text())
    failures = 0
    for feed in manifest["feeds"]:
        name, url = feed["name"], feed["url"]
        status, body = fetch(url)
        if status != 200 or not body:
            print(f"FAIL {name}: http={status}")
            failures += 1
            continue
        detail = f"http=200 size={len(body)}"
        ok = True
        if "json_key" in feed:
            try:
                val = json.loads(body).get(feed["json_key"])
                if not val:
                    ok, detail = False, f"missing/empty key {feed['json_key']}"
            except Exception:
                ok, detail = False, "unparseable JSON"
        if ok and "min_lines" in feed:
            n = len(body.decode("utf-8", "replace").splitlines())
            if n < feed["min_lines"]:
                ok, detail = False, f"only {n} lines"
            else:
                detail += f" lines={n}"
        if ok and "freshness_jsonpath" in feed:
            ok, detail = freshness_ok(body, feed["freshness_jsonpath"], feed["max_age_days"])
        print(f"{'OK  ' if ok else 'FAIL'} {name}: {detail}")
        failures += not ok
    print(f"{'OK' if not failures else 'FAIL'}: {len(manifest['feeds']) - failures}/{len(manifest['feeds'])} feeds healthy.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
