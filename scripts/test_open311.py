#!/usr/bin/env python3
"""Open311 endpoint probe for UK / London-area councils.

Hits discovery.json + services.json on each known endpoint and prints a
summary of what's working. Does NOT POST anything — read-only research.

Usage:
    .venv/bin/python scripts/test_open311.py

Findings as of June 2026 are in docs/open311-endpoints.md.
"""

from __future__ import annotations

import json
import sys
import time
from dataclasses import dataclass
from typing import Any

import requests

USER_AGENT = "Obsidian-Research-Bot/1.0 (Open311 endpoint discovery; civic complaints prototype)"
REQUEST_TIMEOUT = 12
POLITE_DELAY_S = 0.5

# Known mySociety / FixMyStreet co-brand Open311 endpoints serving London authorities,
# plus the central FixMyStreet aggregate. All confirmed live with HTTP 200 + JSON.
ENDPOINTS: list[tuple[str, str]] = [
    # (council/jurisdiction label, base URL — no trailing slash)
    ("FixMyStreet (central, federates to all UK councils)", "https://www.fixmystreet.com/open311"),
    ("Bromley (LBR)",                                       "https://fix.bromley.gov.uk/open311"),
    ("Bexley (LBX)",                                        "https://fix.bexley.gov.uk/open311"),
    ("Royal Greenwich (RBG)",                               "https://fix.royalgreenwich.gov.uk/open311"),
    ("Southwark (LBS)",                                     "https://report.southwark.gov.uk/open311"),
    ("Brent (LBB)",                                         "https://report.brent.gov.uk/open311"),
    ("Hounslow Highways (Hounslow LBR)",                    "https://fms.hounslowhighways.org/open311"),
    # Non-London, included for cross-check that the same pattern works elsewhere
    ("West Northamptonshire (out-of-London control)",       "https://fix.westnorthants.gov.uk/open311"),
]


@dataclass
class ProbeResult:
    label: str
    base_url: str
    discovery_ok: bool
    services_ok: bool
    services_count: int | None
    discovery_contact: str | None
    notes: str = ""


def fetch_json(url: str) -> tuple[int, Any, str]:
    """Return (status_code, parsed_json_or_None, content_type)."""
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    try:
        r = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
    except requests.RequestException as e:
        return 0, None, f"request_error: {e}"
    ct = r.headers.get("Content-Type", "")
    if r.status_code != 200:
        return r.status_code, None, ct
    if "json" not in ct:
        return r.status_code, None, ct
    try:
        return r.status_code, r.json(), ct
    except ValueError:
        return r.status_code, None, ct


def probe_one(label: str, base: str) -> ProbeResult:
    print(f"\n=== {label} ===")
    print(f"base: {base}")

    # 1. discovery.json
    disc_url = f"{base}/v2/discovery.json"
    code, payload, ct = fetch_json(disc_url)
    disc_ok = False
    contact = None
    if code == 200 and isinstance(payload, dict) and "discovery" in payload:
        disc_ok = True
        d = payload["discovery"]
        contact = d.get("contact")
        endpoints = d.get("endpoints", [])
        print(f"  [OK]   discovery.json  HTTP={code}  endpoints={len(endpoints)}  contact={contact!r}")
        if endpoints:
            ep = endpoints[0]
            print(f"         spec={ep.get('specification')}  type={ep.get('type')}  formats={ep.get('formats')}")
    else:
        print(f"  [FAIL] discovery.json  HTTP={code}  ct={ct}")
    time.sleep(POLITE_DELAY_S)

    # 2. services.json
    svc_url = f"{base}/v2/services.json"
    code, payload, ct = fetch_json(svc_url)
    services_ok = False
    services_count: int | None = None
    if code == 200 and isinstance(payload, dict) and "services" in payload:
        services_ok = True
        svcs = payload["services"]
        services_count = len(svcs)
        print(f"  [OK]   services.json   HTTP={code}  count={services_count}")
        # First 10 service codes
        sample = [s.get("service_name") for s in svcs[:10]]
        print(f"         first 10: {sample}")
        # Look for civic-issue categories
        for kw in ["pothole", "fly", "graffiti", "street light", "fly-tip"]:
            matches = [s.get("service_name") for s in svcs if kw.lower() in (s.get("service_name") or "").lower()]
            if matches:
                print(f"         contains '{kw}': {len(matches)} categories (first: {matches[0]!r})")
    else:
        print(f"  [FAIL] services.json   HTTP={code}  ct={ct}")
    time.sleep(POLITE_DELAY_S)

    return ProbeResult(
        label=label,
        base_url=base,
        discovery_ok=disc_ok,
        services_ok=services_ok,
        services_count=services_count,
        discovery_contact=contact,
    )


def main() -> int:
    print("Open311 endpoint probe")
    print(f"UA: {USER_AGENT}")
    print(f"Endpoints to probe: {len(ENDPOINTS)}")

    results: list[ProbeResult] = []
    for label, base in ENDPOINTS:
        results.append(probe_one(label, base))

    print("\n\n=== SUMMARY ===")
    fmt = "{:<55} {:>10} {:>10} {:>10}  {}"
    print(fmt.format("endpoint", "discovery", "services", "count", "contact"))
    print("-" * 130)
    for r in results:
        print(fmt.format(
            r.label[:55],
            "OK" if r.discovery_ok else "FAIL",
            "OK" if r.services_ok else "FAIL",
            r.services_count if r.services_count is not None else "-",
            (r.discovery_contact or "")[:50],
        ))

    ok = sum(1 for r in results if r.discovery_ok and r.services_ok)
    print(f"\n{ok}/{len(results)} endpoints respond with valid Open311 JSON.")
    print("\nNote: POST /requests requires an API key (HTTP 403 otherwise) —")
    print("we did not POST during this run. See docs/open311-endpoints.md.")
    return 0 if ok == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
