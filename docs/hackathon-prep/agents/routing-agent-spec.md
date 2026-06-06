# Agent 03 — Routing

> Owner: **Ongun**. Time budget: **75 min** (13:00–14:15 Saturday).
> Hands off to: submission agent.

---

## What it does

Take the severity-scored issue. Decide **which council** owns the geographic point, **which department** handles the category, and **which channel** to submit through.

```
INPUT
  CivicIssue (with category, latitude, longitude, severity_score)

OUTPUT
  CivicIssue (mutated)
    - borough: str                  # "Camden", "Tower Hamlets", etc.
    - council: str                  # "London Borough of Camden"
    - department: str               # "Highways" / "Waste & Environmental Services"
    - submission_channel: str       # "open311" | "love_clean_streets" | "form" | "email"
    - submission_endpoint: str      # URL or email address
    - submission_metadata: dict     # channel-specific (service_code for Open311 etc.)
```

The submission agent takes this and POSTs.

---

## Decision tree

```
1. Resolve borough from (latitude, longitude)
       ↓
2. Look up (borough, category) in the routing table
       ↓
3a. Open311 endpoint exists?  → channel="open311", endpoint=that URL
3b. Else LCS endpoint exists? → channel="love_clean_streets"
3c. Else bespoke form known?  → channel="form"
3d. Else                      → channel="email", endpoint="contact@<borough>.gov.uk"
```

Step 3a is the win. We chase Open311 because we verified Camden's endpoint live and the pattern holds for ~10 boroughs that run FixMyStreet Pro.

---

## Borough resolution — point in polygon

Two options:

**Option A (preferred):** Download London borough boundaries as GeoJSON from data.london.gov.uk. Use Shapely `Polygon.contains(Point)` to find the borough.

```python
from shapely.geometry import Point, shape
import json

with open("data/london_boroughs.geojson") as f:
    geo = json.load(f)
boroughs = [(f["properties"]["name"], shape(f["geometry"])) for f in geo["features"]]

def find_borough(lat: float, lon: float) -> str | None:
    p = Point(lon, lat)
    for name, poly in boroughs:
        if poly.contains(p):
            return name
    return None
```

**Option B (fallback):** Nominatim reverse geocode. Slower, rate-limited, but doesn't need the GeoJSON file.

Default to A. Pre-download the GeoJSON at scaffolding phase (it's <5 MB).

---

## Routing table — `data/routing_table.json`

For the hackathon we hard-code 33 boroughs × 18 categories. For demo: only Camden + Tower Hamlets + 3 others need real entries; everything else falls through to the email default. Build with help from `bounties/nemotron-bounty-strategy.md` for the bounty-relevant boroughs.

Shape:

```json
{
  "Camden": {
    "Roads and Highways":      { "channel": "open311", "endpoint": "https://fixmystreet.camden.gov.uk/open311/v2/requests.xml", "service_code": "POTHOLE", "department": "Highways" },
    "Waste and Fly-Tipping":   { "channel": "open311", "endpoint": "https://fixmystreet.camden.gov.uk/open311/v2/requests.xml", "service_code": "FLYTIP",   "department": "Waste" },
    "_default":                { "channel": "open311", "endpoint": "https://fixmystreet.camden.gov.uk/open311/v2/requests.xml", "service_code": "OTHER",   "department": "Contact Camden" }
  },
  "Tower Hamlets": {
    "Waste and Fly-Tipping":   { "channel": "form",   "endpoint": "https://forms.towerhamlets.gov.uk/service/Report_a_street_problem", "department": "Waste & Env Services" },
    "_default":                { "channel": "email",  "endpoint": "contactus@towerhamlets.gov.uk", "department": "Contact Us" }
  },
  "Hackney":   { "_default": { "channel": "open311", "endpoint": "https://reportaproblem.hackney.gov.uk/open311/v2/requests.xml", "service_code": "OTHER", "department": "Hackney Council" } },
  "Southwark": { "_default": { "channel": "open311", "endpoint": "https://report.southwark.gov.uk/open311/v2/requests.xml", "service_code": "OTHER", "department": "Southwark Council" } },
  "_default": {
    "_default": { "channel": "email", "endpoint": "contact@<borough_slug>.gov.uk", "department": "Council Contact" }
  }
}
```

The agent looks up `[borough][category]`, falls back to `[borough][_default]`, falls back to `[_default][_default]`.

---

## Tower Hamlets vs Camden — demo-borough handling

Per `decisions-locked.md`: the **demo story** is Tower Hamlets (Rebecca), but the **actual API call** goes to Camden's Open311 sandbox because Tower Hamlets has no Open311.

The routing agent looks up Tower Hamlets honestly. In the orchestrator, we have one special-case for the demo: if `BORROWED_SUBMISSION_TARGET=Camden` env var is set, the submission agent routes the actual POST to Camden but logs both the "real" Tower Hamlets routing decision AND the actual Camden submission. The README discloses this.

---

## Cursor build prompt (paste at 13:00)

```
GOAL: Build the routing agent. Given a CivicIssue with latitude, longitude, and
category, set borough, council, department, submission_channel,
submission_endpoint, and submission_metadata on the issue.

CONSTRAINTS:
- File: src/agents/routing.py
- Borough resolution: point-in-polygon against data/london_boroughs.geojson
  using shapely. If shapely not installed, install with: pip install shapely.
  Pre-load all polygons at module import.
- Routing table: data/routing_table.json (shape per routing-agent-spec.md).
- Lookup: routing_table[borough][category] → fall back to
  routing_table[borough]["_default"] → fall back to routing_table["_default"]["_default"].
- For the catch-all email default, substitute <borough_slug> with lowercase
  hyphenated borough name (e.g. "tower-hamlets").
- council field: "London Borough of " + borough (with City of London handled
  as "City of London Corporation").
- No LLM call. This is pure lookup + tree traversal. Deterministic.
- Persist mutated CivicIssue to processed_issues table.

ACCEPTANCE:
- python -c "
   from src.agents.routing import RoutingAgent
   from src.models.intake import CivicIssue
   issue = CivicIssue(latitude=51.521, longitude=-0.0656,
                     category='Waste and Fly-Tipping',
                     photo_description='', voice_transcript='', photos=[], raw_voice_text='')
   r = RoutingAgent().process(issue)
   assert r.borough == 'Tower Hamlets', f'Got {r.borough}'
   assert r.submission_channel in ['form', 'email']
   print(r.borough, r.submission_channel, r.submission_endpoint)
   "

CONTEXT:
- Look at decisions-locked.md for the Camden-as-submission-sandbox rule.
- The boroughs GeoJSON is pre-downloaded at data/london_boroughs.geojson —
  if missing, fetch from
  https://skgrange.github.io/www/data/london_boroughs.json
- No fancy fallback chain across boroughs ("if Tower Hamlets fails, route to
  Camden") — that's a special-case in the orchestrator, not the routing agent.
- Output must be JSON-serialisable for the dashboard.
```

---

## Failure modes + recovery

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Borough resolves to None | Point outside London or GeoJSON missing | Default to "Camden" + log warning. Beats crashing. |
| Routing table miss | Category not in table | _default chain handles it |
| Open311 endpoint changed | Council CMS update | Pin to email channel for that borough; update later |
| Shapely import error | Library missing | `pip install shapely` — should be in requirements.txt by now |
| Geocoding is slow | Polygon library slow | Pre-load polygons at module import, not per call |

---

## Smoke test (`tests/smoke_routing.py`)

```python
from src.agents.routing import RoutingAgent
from src.models.intake import CivicIssue

cases = [
    # Rebecca — Tower Hamlets fly-tipping
    (CivicIssue(latitude=51.521, longitude=-0.0656, category="Waste and Fly-Tipping",
                photo_description="", voice_transcript="", photos=[], raw_voice_text=""),
     "Tower Hamlets"),
    # Camden pothole
    (CivicIssue(latitude=51.5390, longitude=-0.1426, category="Roads and Highways",
                photo_description="", voice_transcript="", photos=[], raw_voice_text=""),
     "Camden"),
    # Greenwich anything
    (CivicIssue(latitude=51.4826, longitude=0.0077, category="Street Cleaning",
                photo_description="", voice_transcript="", photos=[], raw_voice_text=""),
     "Greenwich"),
]
for issue, expected in cases:
    r = RoutingAgent().process(issue)
    assert r.borough == expected, f"Expected {expected}, got {r.borough}"
    print(f"{r.borough:<20} {r.submission_channel:<20} → {r.submission_endpoint}")
```

---

## Hand-off

Output → **submission agent**. It reads `submission_channel`, `submission_endpoint`, and `submission_metadata` and POSTs. Routing agent's job is done — it's a pure lookup, no LLM, fast.
