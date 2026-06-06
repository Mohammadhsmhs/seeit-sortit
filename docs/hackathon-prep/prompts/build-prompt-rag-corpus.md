# Build Prompt — RAG Corpus Loader

> Paste into Cursor by **Teammate 1** at **10:00 Saturday** (parallel to scraper running). Estimated build time: **60 min** including ~20 min of waiting for downloads.
>
> This produces the 4 lookup tables the severity agent (and the Nemotron bounty) reads from. Without these the severity agent has nothing to cite.

---

## What you're about to build

A single script `src/data/build_rag_corpus.py` that:

1. Downloads 4 London open datasets (STATS19, schools, hospitals, Census density)
2. Filters each to Greater London
3. Loads each into a dedicated SQLite table with `name`, `latitude`, `longitude`, `extra_json` columns
4. Verifies row counts at the end

That's it. **No embeddings, no vector DB.** Proximity is geometric — the severity agent runs `haversine_m` queries against these tables.

---

## Paste this prompt into Cursor

```
GOAL: Build src/data/build_rag_corpus.py — a one-shot script that downloads
4 London open datasets and loads them into SQLite tables so the severity
agent can query for nearby facts (geometric proximity).

CONSTRAINTS:
- File: src/data/build_rag_corpus.py
- Output DB: same scraper/fixmystreet.db — add 4 new tables alongside the
  existing reports/updates tables
- Tables (each with the same shape):
  rag_collisions(id PRIMARY KEY, name, latitude REAL, longitude REAL,
                 severity TEXT, year INTEGER, extra_json TEXT)
  rag_schools(id PRIMARY KEY, name, latitude REAL, longitude REAL,
              phase TEXT, urn INTEGER, extra_json TEXT)
  rag_hospitals(id PRIMARY KEY, name, latitude REAL, longitude REAL,
                ods_code TEXT, type TEXT, extra_json TEXT)
  rag_lsoa(code TEXT PRIMARY KEY, name, latitude REAL, longitude REAL,
           density REAL, population INTEGER, area_km2 REAL, extra_json TEXT)
  Each table indexed on (latitude, longitude)

- Data sources (download URLs may shift — print clearly which file each
  step is fetching):
  1. STATS19 (collisions): TfL Collision Statistics from
     https://data.london.gov.uk/dataset/road-casualties-severe-injuries-borough/
     Filter to events in last 5 years.
  2. GIAS schools: https://www.get-information-schools.service.gov.uk/
     Downloads/Generate / "All establishment data" CSV. Filter
     Establishment Status=Open AND postcode starts with London prefixes.
  3. NHS hospitals: https://digital.nhs.uk/services/organisation-data-service/
     export.csv URL — filter "London" region.
  4. Census 2021 LSOA density: London Datastore LSOA 2021 population
     density Excel. Filter London LSOAs (codes starting "E01000" through
     "E01005" generally — verify against actual file).

- Download each file once and cache to data/raw/{dataset}.csv|xlsx. Skip
  re-download if file exists and is non-empty.

- For each dataset:
  - Parse with pandas (pip install pandas openpyxl)
  - Convert any Easting/Northing to lat/lon if needed (TfL data uses
    Easting/Northing — use pyproj BNG → WGS84)
  - Drop rows with missing coordinates
  - Insert into the corresponding SQLite table

- At end: print row counts:
  rag_collisions: <N>
  rag_schools: <N>
  rag_hospitals: <N>
  rag_lsoa: <N>
  Total: <N>

- ALL of this must complete in under 15 minutes. Use multiprocessing only
  if absolutely needed.

ACCEPTANCE:
- python -m src.data.build_rag_corpus
- After completion, run:
  sqlite3 scraper/fixmystreet.db "SELECT COUNT(*) FROM rag_schools;"
  > 2000  (London has ~2400 schools)
  sqlite3 scraper/fixmystreet.db "SELECT COUNT(*) FROM rag_collisions;"
  > 5000  (5 years of London)
  sqlite3 scraper/fixmystreet.db "SELECT COUNT(*) FROM rag_lsoa;"
  > 4000  (London has ~4800 LSOAs)
- A spot check query works:
  sqlite3 scraper/fixmystreet.db "SELECT name FROM rag_schools
    WHERE latitude BETWEEN 51.52 AND 51.53
      AND longitude BETWEEN -0.07 AND -0.06 LIMIT 5;"
  Returns names like "Osmani Primary School" (Tower Hamlets / Vallance Rd
  area)

CONTEXT:
- decisions-locked.md: SQLite is the only data store. No vector DB.
- nemotron-bounty-strategy.md mandates citation quality — schools and
  hospitals need NAMES not just IDs. Don't drop the name column.
- The severity agent (agents/severity-agent-spec.md) reads from these
  tables with haversine_m(...) < threshold queries. No fancy indexing —
  full scans within ~5000 rows per table are fast.
- TfL STATS19 uses British National Grid (EPSG:27700). Use pyproj:
    from pyproj import Transformer
    bng = Transformer.from_crs("EPSG:27700", "EPSG:4326", always_xy=True)
    lon, lat = bng.transform(easting, northing)
- If a download URL has changed, print the broken URL clearly and exit 1.
  Don't silently skip a dataset.
```

---

## Common AI corrections

| If AI generates | Correct with |
|-----------------|--------------|
| FAISS / Chroma vector index | "No embeddings — geometric distance only" |
| Sentence-transformers | "No embeddings" |
| `requests.get(url).text` for big files | "Stream with `requests.get(url, stream=True)` and iter_content" |
| Skips Easting/Northing conversion | "STATS19 needs pyproj BNG→WGS84 transform" |
| Logs everything as DEBUG | "Print one line per dataset showing progress + final count" |
| Tries to load directly into pandas without local cache | "Always cache to data/raw/* first" |

---

## After the script works

1. **Verify Osmani Primary appears.** That's Rebecca's neighbour school. If we can't find it, the demo citation won't match the script.

   ```bash
   sqlite3 scraper/fixmystreet.db "SELECT name, latitude, longitude FROM rag_schools WHERE name LIKE '%Osmani%';"
   ```

2. **Add a quick haversine helper test** to confirm proximity queries work:

   ```bash
   python -c "
   from src.utils.geo import haversine_m
   d = haversine_m(51.521, -0.0656, 51.5234, -0.0673)  # Osmani approx
   print(f'~{d:.0f}m')   # expect single hundreds
   "
   ```

3. **Commit and message** `#sorted` with the row counts.

---

## Time budget

- AI generation: 10 min
- First test run with fixes: 20 min
- Download wait (most time spent here): 15-20 min
- Verification queries: 5 min

Total: **~60 min**. If you're past 90 min and haven't all 4 datasets loaded — **drop the slowest** and document the gap in the README. Hospitals are most cuttable (we use them mostly for severity, schools matter more for the citation quality).

---

## Hand-off

The severity agent (`src/agents/severity.py`) reads from these tables. The build-prompt-severity is independent of this, but **severity's smoke test will fail if these tables are empty**. Make sure they're loaded before severity is built or your time estimates explode.
