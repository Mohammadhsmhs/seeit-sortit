# Build Prompt — FixMyStreet Scraper

> Paste into Cursor by **Teammate 1** at **09:30 Saturday** (first task of the day). Estimated build time: **75 min** for the scraper + 30 min waiting for first borough's full run.
>
> Why this is first: nothing else has data. The scraper + the DB it fills is the bedrock. Start it running on Islington in the background while you build the dashboard.

---

## What you're about to build

Two Python files:

1. `scraper/db.py` — SQLite schema + helpers
2. `scraper/scrape.py` — the actual scraper, plus a multi-borough runner

Plus a `requirements.txt` and a 100-report Islington dataset in `scraper/fixmystreet.db` by 11:00.

---

## Paste this prompt into Cursor

```
GOAL: Build a polite, idempotent scraper for fixmystreet.com that downloads
public civic reports from London boroughs and stores them in SQLite for our
agent pipeline + dashboard.

CONSTRAINTS:

1. Two files: scraper/db.py and scraper/scrape.py. Plus requirements.txt
   listing: requests>=2.31, beautifulsoup4>=4.12, lxml>=5.0.

2. Respect robots.txt: minimum 3-second delay between ALL requests. Custom
   User-Agent: "LondonCivicAgent-Scraper/0.1 (hackathon research project)".

3. URL patterns:
   - Listing:  https://www.fixmystreet.com/reports/{Borough}?p={page}
     Optional &status=fixed or &status=open.
     100 reports per page. Borough URL slug = borough name with spaces
     replaced by + (e.g. "Tower+Hamlets").
   - Detail:   https://www.fixmystreet.com/report/{id}

4. From listing page: every <li data-report-id="..."> has the report id and
   a data-lastupdate attribute. Title in h3.item-list__heading. Address in
   span.visuallyhidden.

5. From detail page:
   - title:        <h1>
   - category:     regex r"in the (.+?) category" against the full page text
   - description:  .moderate-display p (handle multi-paragraph case)
   - lat/lon:      attributes data-latitude / data-longitude on the map div
   - council:      regex r"Sent to (.+?Council)"
   - reported date: regex r"at (\d{2}:\d{2}),\s+\w+\s+(\d{1,2}\s+\w+\s+\d{4})"
                    parsed via strptime "%d %B %Y %H:%M"
   - photos:       all img with /photo/ in src — normalise to full URL
                    (strip .{n}.fp suffix to get full-size)
   - updates:      every .item-list__item--updates element. Get raw text
                    and parse a timestamp out of it with the same regex
                    as reported date.

6. Resolution detection: scan updates for the literal phrase
   "State changed to: Fixed". If found, the update's timestamp is resolved_at.
   Compute resolution_days = (resolved_at - created_at).total_seconds() / 86400.

7. SQLite schema in db.py:
   reports(id INTEGER PRIMARY KEY, title, category, description, latitude REAL,
           longitude REAL, address, borough, council, status TEXT,
           created_at, updated_at, resolved_at, resolution_days REAL,
           photo_urls TEXT, scraped_at TEXT DEFAULT datetime('now'))
   updates(id INTEGER PRIMARY KEY AUTOINCREMENT, report_id, text, timestamp,
           FOREIGN KEY (report_id) REFERENCES reports(id))
   Indexes on borough, category, status, created_at, (latitude, longitude).

8. Idempotent: ON CONFLICT(id) DO UPDATE for reports — re-running the
   scraper skips rows already present (check existence before fetching the
   detail page, so we don't waste the 3-second budget).

9. CLI in scrape.py:
   python scrape.py <Borough> [--status fixed|open] [--max-pages N]

10. ALSO write scrape_london.py that loops over a hardcoded list of all 33
    boroughs. 1 page of fixed + 1 page of open per borough. Print progress.

CONSTRAINTS WE LEARNED THE HARD WAY:
- FixMyStreet has NO <time datetime="..."> elements. Date parsing must be
  text-based.
- "City of London Corporation" is the URL slug for the Square Mile.
- The dataset Wikipedia/research call "Enfield Southgate" doesn't exist
  post-2024 — skip it.
- Description sometimes contains line breaks; preserve them.
- The Council pattern can over-match — use the non-greedy regex above.

ACCEPTANCE:
- pip install -r scraper/requirements.txt
- python scraper/scrape.py Islington --status fixed --max-pages 1
- After ~5 minutes (100 reports × 3 sec + parsing), check:
  sqlite3 scraper/fixmystreet.db
    "SELECT COUNT(*) FROM reports WHERE borough='Islington';"
  > 95
  "SELECT COUNT(*) FROM reports WHERE latitude IS NOT NULL;"
  > 90
  "SELECT COUNT(*) FROM updates;"
  > 50

Then start scrape_london.py in the background. Move on to dashboard work
(build-prompt-dashboard.md) while it runs.

CONTEXT:
- decisions-locked.md: SQLite, no Postgres, no ORM, vanilla Python.
- requirements.txt lives at scraper/requirements.txt, not project root.
- Photos are URLs — we DO NOT download photos to disk in this scraper.
  A separate script (build-prompt-download-photos.md if created) handles
  that. Photos sit as URLs in photo_urls JSON column for now.
- The robots.txt 3-sec delay is non-negotiable. Faster looks aggressive.
```

---

## After the scraper works

Don't move on without these checks:

1. **Run the SQL acceptance queries.** All three must pass.
2. **Inspect one record** with the most data:
   ```bash
   sqlite3 scraper/fixmystreet.db -line "SELECT * FROM reports WHERE photo_urls IS NOT NULL LIMIT 1;"
   ```
   Verify: title makes sense, category is one of our 18, lat/lon are in London (~51.4-51.6 / -0.5-0.3), photo_urls is a JSON array of HTTPS strings.
3. **Start the long-running scrape** in a different terminal:
   ```bash
   python scraper/scrape_london.py &
   ```
   This will run for ~50 minutes. Don't wait — go build the dashboard.

---

## Common AI corrections

| If AI generates | Correct with |
|-----------------|--------------|
| `asyncio` + `aiohttp` | "Use synchronous requests — robots.txt rate-limits us anyway" |
| `time.sleep(1)` | "3 seconds minimum per robots.txt — non-negotiable" |
| Downloads photos to disk | "Just store URLs in photo_urls JSON column" |
| Catches all exceptions silently | "Print the URL + exception, skip that report, continue" |
| Uses xml.etree to parse pages | "Use BeautifulSoup with lxml parser" |
| Writes ORM models (SQLAlchemy) | "Plain sqlite3 with parameterised queries" |

---

## Time budget

- AI generation: 10 min
- Acceptance fixes: 15 min
- Islington one-page test: ~5 min wait
- Full London background scrape kickoff: 2 min
- Total before moving on to dashboard: **~30 min real time, scraper running in background for the next hour**

---

## Hand-off

Other components read from `scraper/fixmystreet.db`:
- Dashboard reads from `reports` table
- RAG retrieval reads from the LSOA / schools tables (different scraper — see `prompts/build-prompt-rag-corpus.md`)
- Agent pipeline writes to `processed_issues` (built by orchestrator)

Single source of truth, one file, easy to back up.
