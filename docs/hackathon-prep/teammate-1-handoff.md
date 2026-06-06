41# London Civic Agent — Teammate Handoff (Saturday Morning Tasks)

> **What this is.** A complete product spec + sequenced prompt list so you can build the data + UI layer of our hackathon project on Saturday morning while Ongun starts on the agent pipeline.
>
> **Time budget.** ~4 hours focused work. Tasks 1-3 are essential; tasks 4-6 are stretch.
>
> **Tools you'll use.** Cursor or Claude Code (whichever you prefer). Each task is a self-contained prompt — paste it, let the AI generate the code, then verify with the acceptance check before moving on.

---

## 1. Product brief — what we're building

**Pitch in one sentence:** Every Londoner just got a £200/hour ombudsman that takes one photo and one voice note and doesn't stop chasing the council until your pothole gets fixed.

**The problem.** Reporting a civic issue in London (pothole, fly-tip, broken streetlight, abandoned vehicle) currently takes 8–10 clicks across 67–146 category options. Different councils use different platforms (FixMyStreet, Love Clean Streets, bespoke portals). Worst of all: after submitting, residents hear nothing back, even when work is being done. Most give up.

**Our system.** A multi-agent AI that:
1. Takes a photo + voice note from the resident
2. Classifies the issue from the photo (vision model)
3. Scores severity using cited London open data (collisions, schools, hospitals, footfall, census density)
4. Identifies the correct council + department
5. Files the report directly to council CRMs via Open311
6. Tracks SLA — if breached, escalates by phone using ElevenLabs voice agent
7. If still ignored, drafts a formal complaint to the Local Government Ombudsman and MP
8. Publishes a **public council leaderboard** ranking borough performance fairly (using a multi-dimensional scorecard)

**Why this wins.** Existing tools (FixMyStreet, CivicDesk) are better forms. They route the report and stop. We close the loop — track, call, escalate, hold publicly accountable. The leaderboard is the killer feature: it's the accountability layer none of our competitors have.

**Hackathon constraints.**
- NVIDIA Hack for Impact London, 5–7 June 2026
- Must run on the provided DGX Spark / ASUS GX10 hardware
- Must use London Datastore / TfL / open data
- Must be agentic (multi-agent, not a chatbot)
- Sponsors: NVIDIA, HP, Nebius, ElevenLabs
- 3-minute demo on Sunday afternoon

---

## 2. Architecture (high level)

```
┌──────────────────────────────────────────────────────────────────┐
│                       USER (resident)                            │
│           snaps photo + records voice note                       │
└──────────────────────────┬───────────────────────────────────────┘
                           │
            ┌──────────────┴───────────────┐
            │                              │
        Intake Agent              Voice STT (ElevenLabs Scribe)
   (vision model classifies)
            │
   ┌────────┴────────┐
   │ Severity Agent  │ ← RAG over London Datastore (collisions,
   └────────┬────────┘   schools, hospitals, footfall, census)
            │
   ┌────────┴────────┐
   │  Routing Agent  │ ← borough + category → correct council
   └────────┬────────┘   department + submission channel
            │
   ┌────────┴─────────┐
   │ Submission Agent │ ← Open311 POST to council CRM
   └────────┬─────────┘
            │
   ┌────────┴─────────────┐
   │ Local CRM (SQLite)   │ ← tracks state machine
   └────────┬─────────────┘
            │ if SLA breached
   ┌────────┴──────────┐
   │ Phone Escalation  │ ← ElevenLabs Conversational AI + Twilio
   └────────┬──────────┘
            │ if still unresolved
   ┌────────┴──────────────┐
   │  Further Escalation   │ ← drafts complaints to LGO / MP
   └───────────────────────┘

           ┌────────────────────────────────────┐
           │  PUBLIC DASHBOARD (your job)       │
           │  - Map of reports across London    │
           │  - Council leaderboard (scorecard) │
           │  - Per-borough drill-down          │
           └────────────────────────────────────┘
```

**Tech stack we've decided on:**
- Python 3.11+
- SQLite for data
- Flask for the web dashboard
- Leaflet for maps
- Chart.js for charts
- Plain HTML/CSS/JS for the frontend (no React — keep it lean for the demo)
- All inference runs locally on the DGX Spark via Ollama / NVIDIA NIM

---

## 3. Your lane

You own the **data + UI layer**. That means:
- The scraper (we need to bootstrap our database with real London civic reports)
- The SQLite schema + data pipeline
- The public dashboard (map, leaderboard, ticket detail view)
- Borough-level pages

You are **NOT** responsible for:
- The agent pipeline (intake / severity / routing / etc.) — Ongun is on this
- Model integration (Llama 3.3, Nemotron, NIM)
- Voice / phone integration (ElevenLabs + Twilio)
- The DGX Spark setup

Your work is the **canvas** the agents paint on. Without it, there's nothing visible to demo. Your contribution is the demo.

---

## 4. Setup checklist (30 minutes)

Before you start the tasks:

```bash
# 1. Install Python 3.11 or later if you don't have it
brew install python@3.11

# 2. Install your editor with AI assist
# Either Cursor (https://cursor.com) or use Claude Code in your terminal

# 3. Create the project folder
mkdir ~/london-civic-agent
cd ~/london-civic-agent

# 4. Set up a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 5. Init a git repo
git init
echo ".venv/" > .gitignore
echo "*.db" >> .gitignore
echo "__pycache__/" >> .gitignore
echo "photos/" >> .gitignore

# 6. Create the folder structure
mkdir scraper dashboard data docs
mkdir dashboard/templates dashboard/static
```

You're ready to start.

---

## 5. The task list

Each task below is a prompt you paste into Cursor or Claude Code. Wait for the AI to generate everything, run it, check it works, then move on. Don't skip ahead — task N depends on task N-1.

---

### TASK 1 — FixMyStreet scraper

**Goal.** Scrape ~200 civic reports per London borough from FixMyStreet into a local SQLite database.

**Why it matters.** This is our entire dataset. Without it, the dashboard is empty, the agents have nothing to RAG against, and the scorecard is meaningless. Most important task in your morning.

**Estimated time.** 90 minutes (most of it is the scrape running — you'll start it then move to task 2).

**The prompt to paste:**

```
Build a Python scraper for FixMyStreet (https://www.fixmystreet.com).

Goal: scrape civic reports (potholes, fly-tipping, etc.) from London boroughs and save them to a SQLite database. We need this to bootstrap a London-wide civic dashboard.

Requirements:

1. Two files: scraper/db.py (SQLite schema + helpers) and scraper/scrape.py (the actual scraper).

2. Respect FixMyStreet's robots.txt — minimum 3 second delay between requests. Use a custom User-Agent header that identifies the tool ("LondonCivicScraper/0.1 (hackathon research)").

3. URL structure:
   - Borough listing: https://www.fixmystreet.com/reports/{Borough}?p={page} (paginate via ?p=N, 100 reports per page)
   - Individual report detail: https://www.fixmystreet.com/report/{id}
   - Optional status filter: ?status=fixed or ?status=open

4. From the borough listing page, extract: report id (data-report-id attribute on the li), title, address (span.visuallyhidden), last-updated timestamp (data-lastupdate attribute).

5. For each report, fetch the detail page and extract: title (h1), category (parse from "in the X category" text), description (.moderate-display p), latitude/longitude (data-latitude/data-longitude attributes on map element), council name (parse from "Sent to X Council" text), reported date (parse "at HH:MM, Day D Month YYYY" pattern), photo URLs (img tags with /photo/ in src), all updates/comments (.item-list__item--updates elements, with timestamps).

6. Detect resolution: scan updates for the phrase "State changed to: Fixed" — if found, record resolved_at timestamp and compute resolution_days = resolved_at - created_at.

7. SQLite schema:
   - Table "reports": id (primary key), title, category, description, latitude, longitude, address, borough, council, status (open/fixed), created_at, updated_at, resolved_at, resolution_days, photo_urls (JSON array), scraped_at (default now)
   - Table "updates": id (autoincrement), report_id (foreign key), text, timestamp
   - Indexes on borough, category, created_at, status

8. The scraper should be IDEMPOTENT — re-running it skips reports already in the DB. Use ON CONFLICT(id) DO UPDATE for upserts.

9. Add a CLI: python scrape.py <borough> --status fixed --max-pages 2 — defaults to scraping the most recent reports. Borough name is the FixMyStreet URL slug (e.g. "Camden", "Hackney", "Tower+Hamlets" with space-as-plus handled).

10. Also create scrape_london.py that loops over a hardcoded list of all 33 London boroughs, scraping 1 page of fixed + 1 page of open reports for each. Log progress per borough.

Use requests + BeautifulSoup4 + lxml. Add a requirements.txt with all dependencies. Test your scraper on Islington first (small enough to verify quickly), then expand.

Generate all three files (db.py, scrape.py, scrape_london.py) plus requirements.txt.
```

**Acceptance criteria:**
- After running `python scraper/scrape.py Islington --max-pages 1 --status fixed`, you should see ~100 reports in `scraper/fixmystreet.db`
- Run: `sqlite3 scraper/fixmystreet.db "SELECT COUNT(*), borough FROM reports GROUP BY borough"` → returns rows
- Reports have non-null `latitude`, `longitude`, `category`, and `created_at`

**Then start the big scrape in the background:**
```bash
pip install -r scraper/requirements.txt
python scraper/scrape.py Islington --max-pages 1 --status fixed   # verify it works
python scraper/scrape_london.py &                                   # let this run while you do task 2
```

The full London scrape takes ~50 minutes at 3s per request. Move on to task 2 while it runs.

---

### TASK 2 — Photo downloader

**Goal.** Download photos for the scraped reports so the UI can display them.

**Why it matters.** Photos are the visceral demo moment. A leaderboard with photos of actual dumped mattresses is 10x more compelling than a leaderboard with text alone.

**Estimated time.** 30 minutes (mostly waiting for downloads).

**The prompt to paste:**

```
Build a Python script scraper/download_photos.py that downloads photos from scraped FixMyStreet reports.

Requirements:

1. Read the photo_urls JSON column from the reports table in scraper/fixmystreet.db.

2. For each URL, download the image to scraper/photos/{report_id}_{index}.jpeg. Use the same 3-second crawl delay as the scraper. Use the same User-Agent.

3. Add a new column "photo_paths" to the reports table (use a migration — ALTER TABLE if missing). After downloading, populate this column with a JSON array of local paths so the dashboard can serve them.

4. The script should be idempotent: skip files that already exist on disk and skip rows whose photo_paths is already set.

5. CLI: --borough <name> to filter, --limit <N> to cap, --redo to re-process rows that already have photo_paths set.

6. Log progress every 10 downloads.

Generate the file and an updated db.py if the migration needs to live there.
```

**Acceptance criteria:**
- `ls scraper/photos | wc -l` returns at least 50
- DB column `photo_paths` is populated for the downloaded reports

---

### TASK 3 — Flask dashboard skeleton with map

**Goal.** A web page at `localhost:5050` showing a map of London with a dot for every scraped report.

**Why it matters.** The map is the visual centerpiece of the demo. If a judge sees thousands of red dots scattered across the city, they instantly understand the scale of the problem.

**Estimated time.** 60 minutes.

**The prompt to paste:**

```
Build a Flask dashboard for a London civic reporting dataset.

Folder: dashboard/

Files to create:
- dashboard/app.py — Flask app with routes
- dashboard/templates/index.html — main dashboard page
- dashboard/static/style.css — CSS

Requirements for the Flask app:

1. Load reports from ../scraper/fixmystreet.db (SQLite). Connection helper that returns sqlite3.Row.

2. Routes:
   - GET / → renders index.html
   - GET /api/reports → JSON array of all reports (id, title, category, description, latitude, longitude, address, borough, council, status, created_at, resolved_at, resolution_days, photo_urls). Sorted by created_at DESC.
   - GET /api/reports/<int:id> → single report with all updates from the updates table joined in. Photo URLs parsed from the JSON column into an array. Include a derived fixmystreet_url field pointing to the original report.
   - GET /api/boroughs/summary → list of {borough, total, resolved, open, median_resolution_days} for each borough.

3. Run on port 5050.

Requirements for index.html:

1. Header bar with the app name "London Civic Agent — Public Dashboard" on a dark navy background.

2. KPI strip below the header showing: Total Reports, Boroughs Covered, Categories, Median Resolution Days. Pull from /api/reports + /api/boroughs/summary.

3. A Leaflet map (use the CDN: leaflet@1.9.4) centered on London (51.535, -0.12), zoom 12. Add OpenStreetMap tiles.

4. Plot every report as a coloured circle marker:
   - Green if resolved in < 7 days
   - Amber if resolved in 7-30 days
   - Red if took >30 days OR still open
   - Grey if status unknown

5. Clicking a marker opens a Leaflet popup with: title, category, borough, address, status badge, days-to-resolve (if fixed) or days-open (if open), the first photo if any, and a link to the source on FixMyStreet.

6. A simple borough leaderboard table below the map: rank, borough, total reports, % resolved, median resolution days. Sort by % resolved descending.

Use clean, modern design — sans-serif font (system font stack), subtle shadows, ample white space, a navy/grey palette. No bootstrap, no jQuery, just vanilla JS + Leaflet.

Generate all four files (app.py, index.html, style.css, plus a small dashboard/static/script.js if it keeps things tidier).
```

**Acceptance criteria:**
- `python dashboard/app.py` starts the server on port 5050
- Open `http://localhost:5050` in your browser
- You see a map with hundreds of dots across London
- Clicking a dot shows a popup with the report details
- The borough leaderboard table appears below the map

---

### TASK 4 — Ticket drawer (sleek modal)

**Goal.** Upgrade the popup to a side-drawer modal with a photo carousel and full comments timeline. This is the "premium" UI moment.

**Why it matters.** Judges will click on tickets to investigate. The drawer is the demo's visual quality bar.

**Estimated time.** 45 minutes.

**The prompt to paste:**

```
Upgrade the dashboard to replace the Leaflet popup with a polished side-drawer modal when a marker is clicked.

Requirements:

1. The drawer:
   - Slides in from the right of the screen
   - 540px wide on desktop, full screen on mobile
   - Has a backdrop with a subtle blur (backdrop-filter: blur(4px))
   - Closes via: X button (top right), Esc key, click on backdrop
   - Smooth cubic-bezier transition (300ms)

2. Drawer content (in order top to bottom):

   a) Header section:
      - Eyebrow: category chip + report ID in monospace
      - Title (h2, bold, prominent)
      - Status badges: "Fixed" (green) or "Open" (red), plus "Resolved in X days" or "Open for X days"

   b) Photo carousel (if photos exist):
      - Large image, one at a time, with prev/next arrow buttons that fade in on hover
      - "1 / N" counter in bottom right
      - Clickable dot indicators below
      - Keyboard support: ArrowLeft / ArrowRight
      - Graceful fallback if image fails to load: dark background with "Photo unavailable" message + icon
      - Aspect ratio 4:3, object-fit: contain, dark background

   c) Metadata section (key-value grid):
      - Borough, Council, Address, Reported date, Resolved date (if applicable)

   d) Description section (if present):
      - Section heading + full description text

   e) Council updates / comments timeline:
      - Vertical timeline with a line connecting dots
      - Green dot for updates containing "Fixed" or "Resolved"
      - Grey dot for everything else
      - Each entry: timestamp + comment text
      - Section heading shows count in a badge: "Council Updates 34"

   f) Sticky footer with two buttons:
      - Secondary: "View [Borough] dashboard →" (link to /dashboard/borough/<slug>)
      - Primary: "Open on FixMyStreet →" (navy fill, white text)

3. Wire it to the /api/reports/<id> endpoint. Cache fetched tickets so re-clicks don't re-fetch.

4. Update /api/reports/<id> on the backend to include the full updates array from the updates table, sorted by timestamp ascending.

Sleek startup design language — Linear / Notion / Stripe-style. Specific values: border-radius 6-12px, font sizes 0.7-0.95rem for body, 1.35rem for titles. Use CSS custom properties for colours.

Show me the updated index.html, app.py, and style.css.
```

**Acceptance criteria:**
- Click any marker → drawer slides in from the right
- Carousel works (prev/next, dots, keyboard)
- Comments timeline renders with dots and timestamps
- Esc closes the drawer

---

### TASK 5 — Sortable leaderboard with adoption flags

**Goal.** Make the leaderboard sortable per column with adoption status chips (FixMyStreet Pro / Public / Direct).

**Why it matters.** This is the most-pitched feature. Has to look polished.

**Estimated time.** 40 minutes.

**The prompt to paste:**

```
Upgrade the borough leaderboard with the following features:

1. New endpoint /api/boroughs/leaderboard returning per-borough metrics:
   - borough, total_reports, resolved_count, open_count, pct_resolved, median_resolution_days, avg_resolution_days, fastest_category (lowest avg resolution), slowest_category (highest avg resolution)
   - Filter to categories with at least 3 reports for fastest/slowest
   - Sort by pct_resolved descending by default

2. Add a JSON file dashboard/static/borough_metadata.json with the FixMyStreet adoption flag per borough:
   - "fms_pro": Camden, Hackney, Westminster, Bromley, Bexley, Merton, Hounslow, Barnet, Southwark, Islington
   - "fms_public": everyone else on FixMyStreet
   - "direct_only": Tower Hamlets, City of London Corporation, Kensington and Chelsea, Havering

3. Leaderboard table in the dashboard, sortable by any column. Click a header to sort by it, click again to toggle direction. Show an arrow indicator on the active column.

4. Columns:
   - Rank (gold/silver/bronze badges for top 3)
   - Borough (with → chevron indicating clickable)
   - Adoption chip (green pill "FMS Pro", amber "FMS", grey "Direct")
   - Total reports
   - % resolved (with colour: green ≥80, amber 50-80, red <50)
   - Median days (with colour: green ≤14, amber 14-30, red >30)
   - Fastest category (green chip)
   - Slowest category (red chip)

5. Add a BETA badge next to the leaderboard heading — small red/orange gradient pill — with a tooltip explaining the scoring methodology is still being refined.

6. Clicking a row navigates to /dashboard/borough/<slug>.

Show me the updated app.py, index.html, style.css.
```

**Acceptance criteria:**
- Column sorting works on every header
- Gold/silver/bronze badges visible on top 3
- Adoption chips render in the correct colours
- Row click navigates to the borough page (which Ongun will hook up later)

---

### TASK 6 (STRETCH) — Per-borough drill-down page

**Goal.** A page at `/dashboard/borough/<slug>` showing one borough's reports and stats.

**Estimated time.** 60 minutes.

**The prompt to paste:**

```
Add a per-borough page to the Flask dashboard.

Route: GET /dashboard/borough/<slug> → renders borough.html with the borough name and slug as template variables.

Helpers:
- Borough slug = lowercase, hyphenated, apostrophes stripped (e.g. "Tower Hamlets" → "tower-hamlets")
- Look up the canonical borough name from the slug by querying DISTINCT borough FROM reports

New API endpoints:
- GET /api/borough/<slug>/reports → all reports for this borough as JSON
- GET /api/borough/<slug>/stats → {total, resolved_count, open_count, pct_resolved, median_days, avg_days, category_breakdown (top 12 by count with avg days), slowest_open (top 10 longest-open reports), fastest_resolved (top 10 quickest fixes)}

Borough page layout:
1. Hero section: back link to /, borough name big, "Performance overview" subtitle, council name
2. KPI strip: total, % resolved, median resolution, average resolution, open backlog
3. Map zoomed to this borough showing only its reports (same marker logic + drawer behaviour as the main map)
4. Category breakdown bar chart (Chart.js, horizontal bars, top 12 categories)
5. Resolution time distribution bar chart (buckets: same day, 1-3d, 3-7d, 1-4w, 1-3mo, 3-6mo, 6+ months — coloured green→red)
6. "These need attention" list — top 10 longest-open reports as rows with title, address, days open, link
7. "Fastest resolutions" list — top 10 fastest fixes as a green-themed equivalent

Same drawer modal for ticket clicks. Reuse the styling and JS from the main page.

Show me the borough.html template, app.py additions, and any CSS additions.
```

**Acceptance criteria:**
- Visit `http://localhost:5050/dashboard/borough/camden`
- See KPIs, charts, lists, and a Camden-only map
- Clicking a marker opens the same drawer modal

---

## 6. After you're done

When you've shipped tasks 1-5 (and ideally 6), let Ongun know. Together we'll:
- Smoke-test everything end-to-end
- Wire the leaderboard to a richer scorecard endpoint (Ongun is building this)
- Integrate the agent submissions (Ongun's pipeline writes to the same DB, so reports flow into your dashboard automatically)
- Polish the demo arc

---

## 7. When to ask for help

**Push through:**
- Generic Python errors (import, env, dependency)
- CSS quirks
- "AI generated weird code" — re-prompt with the specific error

**Ask Ongun:**
- Anything about the agent pipeline, model integration, ElevenLabs, NIM
- "Should we do X or Y?" architecture questions
- Anything that touches `src/agents/` or `src/models/` (those are his lane)

---

## 8. Things to keep in mind

- **Don't over-engineer.** No React, no microservices, no Postgres. SQLite + Flask + vanilla JS. This needs to ship in 48 hours.
- **The demo is the deliverable.** Every decision should be "does this make the 3-minute demo better?" If no, skip it.
- **Clean visual design > clever features.** Judges remember polish. They don't remember cleverness.
- **Hackathon rule reminder: build everything fresh.** Don't copy code from anywhere — let the AI generate everything from the prompts above. The prompts describe what to build; the AI writes the code.
- **Commit often.** `git add . && git commit -m "task N done"` after each acceptance criteria passes. Push to a repo so we both have access.

You've got this. Text Ongun any time.

— London Civic Agent team
