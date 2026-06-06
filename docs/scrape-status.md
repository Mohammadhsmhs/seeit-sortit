# Scrape status — London-wide FixMyStreet dataset

_Last updated: 2026-06-02 13:14 (jobs running in background)_

## Coverage

| | Before | In progress | Target |
|---|---|---|---|
| Boroughs covered | 9 | 24 queued, ~3 partial | 33 (all of London) |
| Total reports in DB | 2,374 | 2,509 (climbing) | ~6,000-7,000 |
| Photos downloaded | 98 (in category subdirs) | 50+ new flat files | All ~1,725 reports with photos |

### Boroughs already in DB (>= 150 rows, skipped by resume logic)

Barnet (300), Bromley (300), Camden (300), Greenwich (300), Hackney (300),
Islington (300), Lewisham (176), Southwark (300).

### Boroughs being scraped now

All other London local authorities, scraping both `fixed` and `open` reports
(up to 2 listing pages × 100 reports each per status, so up to 400 candidate
reports per borough — most boroughs return 100-200 within the 12-month window):

- Barking and Dagenham (33 so far)
- Bexley (had 100 from a test scrape; topping up)
- Brent, City of London Corporation, Croydon, Ealing, Enfield,
  Hammersmith and Fulham, Haringey, Harrow, Havering, Hillingdon, Hounslow,
  Kensington and Chelsea, Kingston upon Thames, Lambeth, Merton, Newham,
  Redbridge, Richmond upon Thames, Sutton, Tower Hamlets, Waltham Forest,
  Wandsworth — queued.
- Westminster (98) — will top up after the others (its threshold of 150 is
  enforced but the resume logic accepts boroughs below it).

## Schema changes (`scraper/db.py`)

Added four columns to `reports` table via in-place ALTER TABLE migration
(safe on the existing 2,374-row DB — verified):

| Column | Type | Default | Purpose |
|---|---|---|---|
| `source` | TEXT | `'fixmystreet'` | Labels the upstream system. Indexed. Will let us add 311-style feeds and council APIs later without losing provenance. |
| `source_url` | TEXT | — | Direct URL back to the original report (`https://www.fixmystreet.com/report/{id}`). Backfilled for all existing rows. |
| `report_count` | INTEGER | 1 | Counts how many separate user reports describe the same underlying issue. Defaults to 1; future dedup pass can increment. |
| `photo_paths` | TEXT | — | JSON array of local relative paths (`photos/{report_id}_{n}.jpeg`). Set when the photo downloader has fetched the actual files. |

Additional indexes: `idx_reports_source`, `idx_reports_status` for fast
filtering.

Skipped: `report_lang`. FixMyStreet UK reports are uniformly English and
adding the column now would be over-design. Trivial to add later via the
same `_migrate()` helper when we ingest multilingual feeds.

`upsert_report` updated to write `source`, `source_url`, `report_count`.
`scrape.py` populates these on every new report.

## Running jobs

| Job | PID | Logs | Notes |
|---|---|---|---|
| Borough scrape | see `scraper/logs/scrape_london.pid` | `scraper/logs/scrape_london.log` | Iterates 24 remaining boroughs × {fixed, open}. 3s crawl delay. ~6-9 min/borough. ETA ~3-4 hours total. |
| Photo download | see `scraper/logs/download_photos.pid` | `scraper/logs/download_photos.log` | Walks all rows where `photo_urls IS NOT NULL` and `photo_paths IS NULL`. 3s crawl delay. ~1,650 photos to fetch, ETA ~1.5 hours. |

Both are politely paced — each request waits 3 seconds (FixMyStreet
robots.txt). Re-runs are idempotent: the scraper skips reports already in
the DB, and the photo downloader skips files already on disk.

## Photo layout

Photos are stored at `scraper/photos/{report_id}_{i}.jpeg` (flat layout,
indexed by report id). The DB's `reports.photo_paths` column is the source
of truth — it stores a JSON array of relative paths per report.

The previous 50 photos under `photos/{category}/...` subdirectories
remain — they were back-filled into `photo_paths` during the migration
so they won't be re-downloaded.

## How to check progress

```bash
# Tail logs
tail -f scraper/logs/scrape_london.log
tail -f scraper/logs/download_photos.log

# Borough coverage snapshot
sqlite3 scraper/fixmystreet.db \
  "SELECT borough, COUNT(*) FROM reports GROUP BY borough ORDER BY 2 DESC;"

# Photo coverage
sqlite3 scraper/fixmystreet.db \
  "SELECT COUNT(*) total, \
          SUM(photo_urls IS NOT NULL) with_urls, \
          SUM(photo_paths IS NOT NULL) downloaded \
   FROM reports;"
```

## Expected final state

- ~33 boroughs covered (all of London)
- ~5,000-7,000 reports total (most boroughs landing 100-300 per the 12-month window)
- ~1,700-2,000 photos downloaded locally (only ~70% of reports include photos)
- All rows tagged `source='fixmystreet'` with a working `source_url`

## Bugs fixed during the run

- `scrape.py` cutoff-comparison crashed on naive datetimes when the listing
  page returned a mix of timezone formats (hit on Barking and Dagenham
  `fixed` reports). Fixed by normalising to UTC before comparison.
