# Build Prompt — Public Dashboard

> Paste into Cursor by Teammate 1 at **11:00 Saturday** (after scaffolding). Estimated build time: **2 hours** total for the three Cursor turns described below.
>
> The dashboard is the demo's visible surface. Treat it as the most important UI to ship.

---

## What you're about to build

A Flask web app on port 5050 with:
- A **London map** showing every scraped + processed report as a coloured circle
- A **borough leaderboard** ranked by composite scorecard (BETA badge)
- A **side-drawer modal** that opens when you click any marker — title, status, photo carousel, comments timeline, sticky footer

Build it in **three Cursor turns** so each piece is verifiable. Don't paste all three at once.

---

## Turn 1 — Flask scaffolding + map (30 min)

Paste into Cursor:

```
GOAL: Build the public dashboard for Sorted. Flask app on :5050 that serves
a single page with a Leaflet map of all FixMyStreet reports from
scraper/fixmystreet.db.

CONSTRAINTS:
- Files: dashboard/app.py, dashboard/templates/index.html,
  dashboard/static/style.css
- Flask app loads reports from ../scraper/fixmystreet.db (sqlite3.Row factory)
- Routes:
  - GET / -> render index.html with a list of all reports passed in as JSON
  - GET /api/reports -> JSON array (id, title, category, description, latitude,
    longitude, address, borough, status, created_at, resolved_at,
    resolution_days, photo_urls)
- index.html: Leaflet 1.9 via CDN, OpenStreetMap tiles, centered (51.535, -0.12)
  zoom 12, 480px tall, every report as L.circleMarker. Marker colour:
    green if resolution_days < 7
    amber if resolution_days 7-30
    red if resolution_days > 30 OR status='open'
    grey if no data
- Run on port 5050
- Vanilla JS only — no React, no jQuery
- Clean modern design: system font stack, navy/grey palette, subtle shadows

ACCEPTANCE:
- python dashboard/app.py starts the server
- curl localhost:5050/api/reports returns JSON array (200)
- Browser http://localhost:5050 shows London map with dots
```

After it works, commit. Move to Turn 2.

---

## Turn 2 — Leaderboard + scorecard endpoint (45 min)

```
GOAL: Add the borough leaderboard panel to the dashboard, plus a /api/boroughs/scorecard
endpoint that returns the fair multi-dimensional scorecard.

CONSTRAINTS:
- New endpoint GET /api/boroughs/scorecard returns:
  {
    "beta": true,
    "boroughs": [
      { "borough", "rank", "composite_score", "resolution_rate_score",
        "speed_score", "long_tail_score", "category_rank_score",
        "adoption" ("fms_pro"|"fms_public"|"direct_only"),
        "reports_per_10k", "total_reports" },
      ...
    ]
  }
- Compute in dashboard/scoring.py — 5 dimensions per spec: volume burden,
  resolution rate (>90d window only), speed (median per category averaged),
  long-tail burden (% open >90d), per-category percentile rank.
  Weights: 25% resolution_rate + 30% category_rank + 25% speed +
  20% long_tail. All normalised 0-100.
- Borough metadata in data/borough_metadata.json — population, area_km2,
  adoption flag. Hardcode if absent (Camden=fms_pro, Hackney=fms_pro,
  Tower Hamlets=direct_only, Greenwich=fms_public, etc.)
- Render a table in index.html under the map with columns:
  Rank | Borough | Adoption (chip) | Vol/10k | Score | Resolved | Speed | LongTail | CatRank
  Click any column header to sort.
  Top 3 ranks get gold/silver/bronze badges.
  Score cells colour-coded: green ≥75, amber 50-75, red <50.
- "BETA" badge next to the leaderboard heading. Red-orange gradient pill.

ACCEPTANCE:
- curl localhost:5050/api/boroughs/scorecard returns the shape above
- Leaderboard table renders, sortable on every column
- Adoption chips show correct colours
- Greenwich appears in top 3, Camden mid-pack
```

Commit. Move to Turn 3.

---

## Turn 3 — Ticket drawer modal (45 min)

```
GOAL: Replace the Leaflet popup with a polished side-drawer modal. Click any
map marker → drawer slides in from right. Photo carousel + comments timeline.

CONSTRAINTS:
- Drawer 540px wide on desktop, full-screen on mobile
- Backdrop with backdrop-filter: blur(4px), click backdrop to close
- ESC key closes
- Smooth slide via cubic-bezier 300ms
- Drawer content in order: header (category chip + ID + title + status badge),
  photo carousel, metadata key-value grid (borough, council, address, dates),
  description, council updates timeline, sticky footer (borough page link +
  primary "Open on FixMyStreet" button)
- Carousel: large image, "1/N" counter, ArrowLeft/ArrowRight nav, clickable
  dots. Failed image -> "Photo unavailable" placeholder with icon.
- Timeline: vertical line connecting timestamped dots. Green dot if update
  text contains "fixed" or "resolved".
- New endpoint GET /api/reports/<id> returns the report + a "updates" array
  joined from the updates table (text, timestamp), sorted ascending
- All vanilla JS — no React, no animation libs

ACCEPTANCE:
- Click any marker on the map -> drawer slides in
- Carousel works (arrows, dots, keyboard)
- Comments timeline renders with at least one green dot for any "fixed" event
- ESC closes the drawer
```

Commit. Stop here. Anything more is polish.

---

## After all three turns

Run a stress test:

```bash
# 1. Make sure /api/reports returns >1000 items
curl -s localhost:5050/api/reports | python -c "import json,sys;print(len(json.load(sys.stdin)))"

# 2. Smoke test the borough page-style behaviour
open http://localhost:5050
# Click a marker — drawer opens within 200ms
# Drawer fully renders within 1 sec
# Esc closes it
```

If everything passes, you're done with the dashboard. The agent pipeline (orchestrator) writes to the same DB — new processed_issues rows appear in the API automatically.

---

## Common AI corrections during these turns

| If AI generates | Correct with |
|-----------------|--------------|
| React or Vue | "Vanilla JS only — no React" |
| `npm install` for anything | "No build step. CDN imports only." |
| WebSockets for live updates | "Polling every 30 sec is fine" |
| Inline `<style>` blobs | "All CSS goes in static/style.css" |
| Loading spinners that block UI | "Show data immediately; loading state in panel header only" |
| jQuery in the snippet | "Use vanilla JS — no jQuery" |

---

## Time budget

- Turn 1: 30 min including the AI iterations
- Turn 2: 45 min
- Turn 3: 45 min
- Stress test: 10 min
- Total: ~2 hours

If by 13:00 Saturday you only have Turn 1 working — that's OK, the demo can use just the map. Turns 2 and 3 are improvements, not blockers.
